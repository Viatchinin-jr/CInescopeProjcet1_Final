import allure
from db_models.transaction_model import AccountTransactionTemplate
from utils.data_generator import DataGenerator
from sqlalchemy.orm import Session
import pytest
import random


class TestTransactionDB():

    def test_accounts_transaction_template(self, tx_db_session: Session):
        # Подготовка к тесту
        # Создаем новые записи в базе данных (чтобы точно быть уверенными, что в базе присутствуют данные для тестирования)

        stan = AccountTransactionTemplate(user=f"Stan_{DataGenerator.generate_random_int(10)}", balance=100)
        bob = AccountTransactionTemplate(user=f"Bob_{DataGenerator.generate_random_int(10)}", balance=500)

        # Добавляем записи в сессию
        tx_db_session.add_all([stan, bob])
        # Фиксируем изменения в базе данных
        tx_db_session.commit()

        def transfer_money(session, from_account: str, to_account: str, amount: int) -> None:
        # пример функции, выполняющей транзакцию
        # представим, что она написана на стороне тестируемого сервиса
        # и вызывая метод transfer_money, мы как будто-бы делаем запрос в api_manager.movies_api.transfer_money
            """
            Переводит деньги с одного счета на другой.
            :param session: Сессия SQLAlchemy.
            :param from_account_id: ID счета, с которого списываются деньги.
            :param to_account_id: ID счета, на который зачисляются деньги.
            :param amount: Сумма перевода.
            """
            # получаем счета
            from_acc = session.query(AccountTransactionTemplate).filter_by(user=from_account).one()
            to_acc = session.query(AccountTransactionTemplate).filter_by(user=to_account).one()

            # Проверяем, что на счете достаточно средств
            if from_acc.balance < amount:
                raise ValueError("Недостаточно средств на счете")

            # выполняем перевод
            from_acc.balance -= amount
            to_acc.balance += amount

            # сохраняем изменения
            session.commit()

        # Проверяем начальные балансы
        stan_db = tx_db_session.query(AccountTransactionTemplate).filter_by(user=stan.user).one()
        bob_db = tx_db_session.query(AccountTransactionTemplate).filter_by(user=bob.user).one()
        assert stan_db.balance == 100
        assert bob_db.balance == 500

        # пытаемся перевести 200 (должно упасть)
        with pytest.raises(ValueError):
            transfer_money(tx_db_session, stan.user, bob.user, 200)

        # проверяем, что деньги не изменились
        stan_db.after = tx_db_session.query(AccountTransactionTemplate).filter_by(user=stan.user).one()
        bob_db.after = tx_db_session.query(AccountTransactionTemplate).filter_by(user=bob.user).one()

        assert stan_db.balance == 100
        assert bob_db.balance == 500


        tx_db_session.delete(stan_db.after)
        tx_db_session.delete(bob_db.after)
        # фиксируем изменения в базе данных
        tx_db_session.commit()

    def test_delete_movie_from_db(self, db_helper, super_admin):
        """
        Я так и не понял, исходя из задания какой из тестов мы рефакторим поэтому написал тут с нуля.
        У нас как бы есть тест в test_api_movies, но там как-будто больше проверка API просто.

        Проверка: после удаления фильма через API запись удаляется из БД
        Предусловие: фильм должен существовать в БД (если нет - создаем через БД)
        """

        # 1) Подготовим фильм в ДБ
        movie_data = DataGenerator.generate_random_movie()
        created_in_db = db_helper.create_test_movie(movie_data)
        movie_id = int(created_in_db.id)

        # Убеждаемся, что запись точно есть
        assert db_helper.get_movie_by_id(movie_id) is not None

        try:
            # 2) Удаляем через API (нужен авторизованный пользователь, поэтому super_admin)
            del_resp = super_admin.api.movies_api.delete_movie(movie_id, expected_status=(200, 204))
            assert del_resp.status_code in (200, 204)

            # 3) Проверим, что записи больше нет в БД
            assert db_helper.get_movie_by_id(movie_id) is None

        finally:
            # страховка, на случай если удаление не сработало
            cleanup = db_helper.get_movie_by_id(movie_id)
            if cleanup:
                db_helper.delete_movie(cleanup.id)


@allure.epic("Тестирование транзакций")
@allure.feature("Тестирование транзакций между счетами")
class TestAccountTransactionTemplate:

    @allure.story("Корректность перевода денег между двумя счетами")
    @allure.description("""
    Этот тест проверяет корректность перевода денег между двумя счетами.
    Шаги:
    1. Создание двух счетов: Stan и Bob.
    2. Перевод 200 единиц от Stan к Bob.
    3. Проверка изменения балансов.
    4. Очистка тестовых данных.
    """)
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("qa_name", "Ivan Petrovich")
    @allure.title("Тест перевода денег между счетами 200 рублей")
    def test_accounts_transaction_template(self, db_session: Session):
        # ----- Подготовка к тесту
        with allure.step("Создание тестовых данных в базе данных: счета Stan и Bob"):
            stan = AccountTransactionTemplate(user=f"Stan_{DataGenerator.generate_random_int(10)}", balance=1000)
            bob = AccountTransactionTemplate(user=f"Bob_{DataGenerator.generate_random_int(10)}", balance=500)
            db_session.add_all([stan, bob])
            db_session.commit()

        @allure.step("Функция перевода денег: transfer_money")
        @allure.description("""
            Функция выполняющая транзакцию, имитация вызова функции на стороне тестируемого сервиса
            и вызывая метод transfer_money, мы как-будто делаем запрос в api_manager.movies_api.transfer_money
            """)
        def transfer_money(session, from_account, to_account, amount):
            with allure.step("Получаем счета"):
                from_account = session.query(AccountTransactionTemplate).filter_by(user=from_account).one()
                to_account = session.query(AccountTransactionTemplate).filter_by(user=to_account).one()

            with allure.step("Проверяем, что на счете недостаточно средств"):
                if from_account.balance < amount:
                    raise ValueError("Недостаточно средств на счете")

            with allure.step("Выполняем перевод"):
                from_account.balance -= amount
                to_account.balance += amount

            with allure.step("Сохраняем изменения"):
                session.commit()

        # ----- Тест
        with allure.step("Проверяем начальные балансы"):
            assert stan.balance == 1000
            assert bob.balance == 500

        try:
            with allure.step("Выполняем перевод 200 единиц от stan к bob"):
                transfer_money(db_session, from_account=stan.user, to_account=bob.user, amount=200)

            with allure.step("Проверяем, что балансы изменились"):
                assert stan.balance == 800
                assert bob.balance == 700

        except Exception as e:
            with allure.step("ОШИБКА отката транзакции"):
                db_session.rollback()

            pytest.fail(f"Ошибка при переводе денег: {e}")

        finally:
            with allure.step("Удаляем даннные для тестирования из базы"):
                db_session.delete(stan)
                db_session.delete(bob)
                db_session.commit()


    @allure.title("Тест с перезапусками")
    @pytest.mark.flaky(reruns=3)
    def test_with_retries(self, delay_between_retries):
        with allure.step("Шаг 1: проверка случайного значения"):
            result = random.choice([True, False])
            assert result, "Тест упал, потому что результат False"