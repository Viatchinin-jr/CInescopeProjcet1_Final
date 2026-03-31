import json
import requests
import logging
import os
from typing import Iterable
from constants import RED, GREEN, RESET
from pydantic import BaseModel


class CustomRequester:
    """
    Кастомный реквестер для стандартизации и упрощения отправки HTTP-запросов.
    """
    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    def __init__(self, session: requests.Session, base_url: str) -> None:
        """
        Инициализация кастомного реквестера.

        :param session: Объект requests.Session.
        :param base_url: Базовый URL API.
        """
        self.session = session
        self.base_url = base_url
        self.session.headers = self.base_headers.copy() # тут я не очень понял
        self.headers = self.base_headers.copy()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def send_request(
        self,
        method: str,
        endpoint: str,
        data: dict | BaseModel | None = None,
        expected_status: int | Iterable[int] = 200,
        need_logging: bool = True,
        params: dict | None = None
    ) -> requests.Response:
        """
        Универсальный метод для отправки HTTP-запросов.

        :param method: HTTP метод (GET, POST, PUT, DELETE и т.д.).
        :param endpoint: Эндпойнт (например, "/login").
        :param data: Тело запроса (JSON-данные).
        :param params: Параметры URL (query-параметры).
        :param expected_status: допустимый код или список кодов.
        :param need_logging: Флаг для логирования (по умолчанию True).
        :return: Объект ответа requests.Response.
        """
        if isinstance(data, BaseModel):
            data = json.loads(data.model_dump_json(exclude_unset=True, by_alias=True))
        response = self.session.request(
            method,
            f"{self.base_url}{endpoint}",
            json=data,
            params=params,
            headers=self.headers
        )
        if need_logging:
            self.log_request_and_response(response)

        if isinstance(expected_status, int):
            allowed_statuses = {expected_status}
        else:
            allowed_statuses = set(expected_status)

        if response.status_code not in allowed_statuses:
            raise ValueError(
                f"Unexpected status code:{response.status_code}."
                f"Expected: {allowed_statuses}"
            )

        return response


    def _update_session_headers(self, **kwargs: str) -> None:
        """
        Обновляет заголовки сессии.

        :param kwargs: заголовки в формате ключ=значение.
        """
        self.headers.update(kwargs)  # Обновляем базовые заголовки
        self.session.headers.update(kwargs)  # Обновляем заголовки в текущей сессии

    def log_request_and_response(self, response):
        """
        Логгирование запросов и ответов. Настройки логгирования описаны в pytest.ini
        Преобразует вывод в curl-like (-H хэдэеры), (-d тело)

        :param response: Объект response получаемый из метода "send_request"
        """
        try:
            request = response.request
            headers = " \\\n".join([f"-H '{header}: {value}'" for header, value in request.headers.items()])
            full_test_name = f"pytest {os.environ.get('PYTEST_CURRENT_TEST', '').replace(' (call)', '')}"

            body = ""
            if hasattr(request, 'body') and request.body is not None:
                if isinstance(request.body, bytes):
                    body = request.body.decode('utf-8')
                elif isinstance(request.body, str):
                    body = request.body
                body = f"-d '{body}' \n" if body != '{}' else ''

            self.logger.info(
                f"{GREEN}{full_test_name}{RESET}\n"
                f"curl -X {request.method} '{request.url}' \\\n"
                f"{headers} \\\n"
                f"{body}"
            )

            response_status = response.status_code
            is_success = response.ok
            response_data = response.text
            if not is_success:
                self.logger.info(f"\tRESPONSE:"
                                 f"\nSTATUS_CODE: {RED}{response_status}{RESET}"
                                 f"\nDATA: {RED}{response_data}{RESET}")
        except Exception as e:
            self.logger.info(f"\nLogging went wrong: {type(e)} - {e}")

