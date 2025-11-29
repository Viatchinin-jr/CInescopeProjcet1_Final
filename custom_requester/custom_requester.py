import json
import requests
import logging
import os
from typing import Iterable


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
        self.headers = self.base_headers.copy()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def send_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
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


    def log_request_and_response(self, response: requests.Response) -> None:
        """
        Логирует HTTP-запрос и ответ.

        :param response: Объект ответа requests.Response.
        """
        try:
            request = response.request
            GREEN = '\033[32m'
            RED = '\033[31m'
            RESET = '\033[0m'
            headers = " \\\n".join([f"-H '{header}: {value}'" for header, value in request.headers.items()])
            full_test_name = f"pytest {os.environ.get('PYTEST_CURRENT_TEST', '').replace(' (call)', '')}"

            body = ""
            if hasattr(request, 'body') and request.body is not None:
                if isinstance(request.body, bytes):
                    body = request.body.decode('utf-8')
                body = f"-d '{body}' \n" if body != '{}' else ''

            self.logger.info(f"\n{'=' * 40} REQUEST {'=' * 40}")
            self.logger.info(
                f"{GREEN}{full_test_name}{RESET}\n"
                f"curl -X {request.method} '{request.url}' \\\n"
                f"{headers} \\\n"
                f"{body}"
            )

            response_data = response.text
            try:
                response_data = json.dumps(json.loads(response.text), indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

            self.logger.info(f"\n{'=' * 40} RESPONSE {'=' * 40}")
            if not response.ok:
                self.logger.info(
                    f"\tSTATUS_CODE: {RED}{response.status_code}{RESET}\n"
                    f"\tDATA: {RED}{response_data}{RESET}"
                )
            else:
                self.logger.info(
                    f"\tSTATUS_CODE: {GREEN}{response.status_code}{RESET}\n"
                    f"\tDATA:\n{response_data}"
                )
            self.logger.info(f"{'=' * 80}\n")
        except Exception as e:
            self.logger.error(f"\nLogging failed: {type(e)} - {e}")
