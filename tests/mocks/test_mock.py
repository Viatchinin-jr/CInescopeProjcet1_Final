class Database:
    def get_user(self, user_id):
        # Реальный код для получения пользователя из базы данных
        pass

import pytest

class StubDatabase:
    def get_user(self, user_id):
        return {"id": user_id, "name": "John Doe"}

def test_get_user():
    db = StubDatabase()
    user = db.get_user(1)
    assert user["name"] == "John Doe"


class EmailService:
    def send_email(self, to, subject, body):
        # Реальный код для отправки email
        pass


from unittest.mock import Mock


def test_send_email():
    email_service = Mock()
    email_service.send_email("user@example.com", "Hello", "This is a test email")

    email_service.send_email.assert_called_once_with("user@example.com", "Hello", "This is a test email")
