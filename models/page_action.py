from playwright.sync_api import Page
import allure



class PageAction:
    """
    Базовый класс, содержащий низкоуровневые обертки над методами Playwright.
    Используется как фундамент для всех Page Object страниц.
    """
    def __init__(self, page: Page):
        self.page = page

    @allure.step("Переход на страницу: {url}")
    def open_url(self, url: str):
        """
        Открывает указанную страницу.
        """
        self.page.goto(url)

    @allure.step("Ввод текста '{text}' в поле '{locator}'")
    def enter_text_to_element(self, locator,  text: str):
        """
        Универсальный метод для ввода текста
        """
        if isinstance(locator, str):
            self.page.fill(locator, text)
        else:
            locator.fill(text)

    @allure.step("Клик по элементу '{locator}'")
    def click_element(self, locator: str):
        """Выполняет обычный клик по элементу."""
        self.page.click(locator)

    @allure.step("Ожидание загрузки страницы: {url}")
    def wait_redirect_for_url(self, url: str):
        """
        Ожидает изменения URL и проверяет его на соответствие ожидаемому.
        Помогает ловить ошибки медленного редиректа.
        """
        self.page.wait_for_url(url)
        assert self.page.url == url, "Редирект на домашнюю старницу не произошел"

    @allure.step("Получение текста элемента: {locator}")
    def get_element_text(self, locator: str) -> str:
        return self.page.locator(locator).text_content()

    @allure.step("Ожидание появления или исчезновения элемента: {locator}, state = {state}")
    def wait_for_element(self, locator: str, state: str = "visible"):
        self.page.locator(locator).wait_for(state=state)

    @allure.step("Скриншот текущей страиницы")
    def make_screenshot_and_attach_to_allure(self):
        screenshot_path = "screenshot.png"
        self.page.screenshot(path=screenshot_path, full_page=True)

        with open(screenshot_path, "rb") as file:
            allure.attach(file.read(), name="Screenshot after redirect", attachment_type=allure.attachment_type.PNG)

    @allure.step("Проверка всплывающего сообщения c текстом: {text}")
    def check_pop_up_element_with_text(self, text: str) -> bool:
        with allure.step("Проверка появления алерта с текстом: '{text}'"):
            notification_locator = self.page.get_by_text(text)
            notification_locator.wait_for(state="visible")
            assert notification_locator.is_visible(), "Уведомление не появилось"

        with allure.step("Проверка исчезновения алерта с текстом: '{text}'"):
            notification_locator.wait_for(state="hidden")
            assert notification_locator.is_visible() == False, "Уведомление не исчезло"


class BasePage(PageAction):
    def __init__(self, page: Page):
        super().__init__(page)
        self.home_url = "https://dev-cinescope.coconutqa.ru/"

        self.home_button = "a[href='/' and text()='Cinescope']"
        self.all_movies_button = "a[href='/movies' and text()='Все фильмы']"

    @allure.step("Переход на главную страницу, из шапки сайта")
    def go_to_home_page(self):
        self.click_element(self.home_button)
        self.wait_redirect_for_url(self.home_url)

    @allure.step("Переход на страницу 'Все фильмы, из шапки сайта'")
    def go_to_all_movies(self):
        self.click_element(self.all_movies_button)
        self.wait_redirect_for_url(f"{self.home_url}movies")


class CinescopRegisterPage(BasePage):
    """
    Класс страницы регистрации.
    Содержит локаторы по ролям и методам для взаимодействия с формой создания аккаунта.
    """
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.home_url}register"

        self.full_name_input = self.page.get_by_role("textbox", name="Имя Фамилия Отчество")
        self.email_input = self.page.get_by_role("textbox", name="Email")
        self.password_input = self.page.get_by_role("textbox", name="Пароль", exact=True)
        self.repeat_password_input = self.page.get_by_role("textbox", name="Повторите пароль")

        self.register_button = self.page.get_by_role("button", name="Зарегистрироваться")
        self.sign_button = self.page.get_by_role("button", name="Войти")

    @allure.step("Открыть страницу регистрации")
    def open(self):
        """Переходит по прямому URL страницы регистрации."""
        self.open_url(self.url)

    @allure.step("Заполнение формы регистрации пользователя")
    def register(self, full_name: str, email: str, password: str, confirm_password: str):
        """
        """
        self.enter_text_to_element(self.full_name_input, full_name)
        self.enter_text_to_element(self.email_input, email)
        self.enter_text_to_element(self.password_input, password)
        self.enter_text_to_element(self.repeat_password_input, confirm_password)

        with allure.step("Нажать кнопку 'Зарегистрироваться'"):
            self.register_button.click()

    @allure.step("Проверка редиректа на страницу входа")
    def assert_was_redirect_to_login_page(self):
        """Проверяет, что после регистрации перекинуло на /login."""
        self.wait_redirect_for_url(f"{self.home_url}login")

    @allure.step("Проверка появления алерта об успешной регистрации")
    def assert_allert_was_pop_up(self):
        self.check_pop_up_element_with_text("Подтвердите свою почту")


class CinescopLoginPage(BasePage):
    """Класс страницы авторизации. Содержит методы для входа в систему и проверки успешного редиректа."""
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.home_url}login"

        self.email_input = self.page.get_by_role("textbox", name="Email")
        self.password_input = self.page.get_by_role("textbox", name="Пароль")

        self.login_button = self.page.locator("form").get_by_role("button", name="Войти")
        self.register_button = self.page.get_by_role("link", name="Зарегистрироваться")

    @allure.step("Открыть страницу входа")
    def open(self):
        self.open_url(self.url)

    @allure.step("Авторизация под пользователем")
    def login(self, email: str, password: str):
        self.enter_text_to_element(self.password_input, password)
        self.enter_text_to_element(self.email_input, email)

        self.login_button.click()

    @allure.step("Проверка редиректа на главную страницу")
    def assert_was_redirect_to_home_page(self):
        self.wait_redirect_for_url(self.home_url)


    @allure.step("Проверка уведомления об успешном входе.")
    def assert_allert_was_pop_up(self):
        self.check_pop_up_element_with_text("Вы вошли в аккаунт")



class MainPage(BasePage):
    """Класс для главной страницы сайта. Управляет навигацией по списку фильмов и переходом в профиль."""
    def __init__(self, page: Page):
        super().__init__(page)
        self.movie_details_button = self.page.get_by_role("button", name="Подробнее")
        self.to_profile_button = self.page.get_by_role("button", name="Профиль")
        self.show_more_button = self.page.get_by_role("button", name="Показать еще")

    @allure.step("Открыть карточку первого фильма")
    def open_first_movie(self):
        self.movie_details_button.first.click()


class MoviePage(BasePage):
    """Класс страницы конкретного фильма. Позволяет взаимодействовать с формой отзывов и рейтинга."""
    def __init__(self, page):
        super().__init__(page)

        self.review_input = self.page.get_by_role("textbox", name="Написать отзыв")
        self.rating_set = self.page.get_by_role("combobox")
        self.send_review_button = self.page.get_by_role("button", name="Отправить")

    @allure.step("Заполнить текст отзыва")
    def enter_review_text(self, text: str):
        self.review_input.fill(text)

    @allure.step("Выбрать оценку")
    def select_rating(self, rating: int):
        self.rating_set.click()
        self.page.get_by_role("option", name=str(rating), exact=True).click()


    @allure.step("Нажать кнопку 'Отправить'")
    def send_review(self):
        self.send_review_button.click()

