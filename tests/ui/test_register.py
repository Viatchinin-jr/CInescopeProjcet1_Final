import time
from playwright.sync_api import sync_playwright, Page
import pytest
import allure
from models.page_action import CinescopRegisterPage
from utils.data_generator import DataGenerator


@allure.epic("Тестирование UI")
@allure.feature("Регистрация")
@pytest.mark.ui
class TestRegisterPage:

   @allure.title("Проведение успешной регистрации")
   def test_register_by_ui(self, page: Page):
       """
       Тест проверяет полный цикл регистрации пользователя:
       от генерации данных до проверки уведомления.
       """
       register_page = CinescopRegisterPage(page)

       with allure.step("Генерация тестовых данных"):
           random_email = DataGenerator.generate_random_email()
           random_name = DataGenerator.generate_random_name()
           random_password = DataGenerator.generate_random_password()

       with allure.step("Открытие страницы и заполнение формы"):
           register_page.open()
           register_page.register(random_name, random_email, random_password, random_password)

       with allure.step("Верификация регистрации и проверка алертов"):
           register_page.assert_was_redirect_to_login_page()
           register_page.make_screenshot_and_attach_to_allure()
           register_page.assert_allert_was_pop_up()

