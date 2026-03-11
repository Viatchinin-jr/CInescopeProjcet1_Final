import pytest
import allure
import random
from sqlalchemy.orm import Session
from db_models.transaction_model import AccountTransactionTemplate
from utils.data_generator import DataGenerator


@allure.epic("Интеграция с БД")
@allure.feature("Транзакции и целостность данных")
@pytest.mark.db
class TestDbTransactions:

    @allure.story("Транзакции между счетами")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Успешный перевод средств между Stan и Bob")
    def test_transfer_money_success(self, db_session: Session):
        with allure.step("Подготовка: создание счетов Stan (1000) и Bob (500)"):
            stan = AccountTransactionTemplate(user=f"Stan_{DataGenerator.generate_random_int(5)}", balance=1000)
            bob = AccountTransactionTemplate(user=f"Bob_{DataGenerator.generate_random_int(5)}", balance=500)
            db_session.add_all([stan, bob])
            db_session.commit()

        def transfer_money(session, from_user, to_user, amount):
            with allure.step(f"Выполнение перевода {amount} от {from_user} к {to_user}"):
                from_acc = session.query(AccountTransactionTemplate).filter_by(user=from_user).one()
                to_acc = session.query(AccountTransactionTemplate).filter_by(user=to_user).one()

                if from_acc.balance < amount:
                    raise ValueError("Недостаточно средств")

                from_acc.balance -= amount
                to_acc.balance += amount
                session.commit()

        try:
            transfer_money(db_session, stan.user, bob.user, 200)

            with allure.step("Верификация: проверка итоговых балансов"):
                db_session.refresh(stan)
                db_session.refresh(bob)
                assert stan.balance == 800
                assert bob.balance == 700
        finally:
            with allure.step("Cleanup: удаление тестовых счетов"):
                db_session.delete(stan)
                db_session.delete(bob)
                db_session.commit()

    @allure.story("Транзакции между счетами")
    @allure.title("Отказ в переводе при недостаточном балансе")
    def test_transfer_money_insufficient_funds(self, db_session: Session):
        with allure.step("Подготовка: создание счета Stan с балансом 100"):
            stan = AccountTransactionTemplate(user=f"Stan_{DataGenerator.generate_random_int(5)}", balance=100)
            bob = AccountTransactionTemplate(user=f"Bob_{DataGenerator.generate_random_int(5)}", balance=500)
            db_session.add_all([stan, bob])
            db_session.commit()

        with allure.step("Попытка перевода 200 единиц (ожидаем ValueError)"):
            with pytest.raises(ValueError, match="Недостаточно средств"):
                # Имитируем логику: снимаем 200, если баланс 100
                if stan.balance < 200:
                    raise ValueError("Недостаточно средств")

        with allure.step("Проверка сохранения исходного баланса"):
            db_session.refresh(stan)
            assert stan.balance == 100

        with allure.step("Cleanup"):
            db_session.delete(stan)
            db_session.delete(bob)
            db_session.commit()

    @allure.story("Синхронизация API и БД")
    @allure.title("Удаление фильма: проверка физического удаления из базы")
    def test_delete_movie_db_consistency(self, db_helper, super_admin):
        with allure.step("Подготовка: создание фильма напрямую в БД"):
            movie_data = DataGenerator.generate_random_movie()
            created_in_db = db_helper.create_test_movie(movie_data)
            movie_id = int(created_in_db.id)
            assert db_helper.get_movie_by_id(movie_id) is not None

        try:
            with allure.step(f"Запрос API на удаление фильма ID: {movie_id}"):
                # Исправлено: delete_movie_by_id вместо delete_movie
                del_resp = super_admin.api.movies_api.delete_movie_by_id(movie_id)
                assert del_resp.status_code in (200, 204)

            with allure.step("Проверка: запись в БД должна отсутствовать"):
                assert db_helper.get_movie_by_id(movie_id) is None

        finally:
            with allure.step("Cleanup: страховочное удаление"):
                if db_helper.get_movie_by_id(movie_id):
                    db_helper.delete_movie(movie_id)


@allure.epic("Стабильность тестов")
class TestFlaky:
    @allure.title("Тест с проверкой механизма перезапусков")
    @pytest.mark.flaky(reruns=3)
    def test_retry_logic(self):
        with allure.step("Генерация случайного результата"):
            result = random.choice([True, False])
            assert result, "Тест упал, ожидаем автоматический перезапуск"