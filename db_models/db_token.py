from sqlalchemy import Column, String, DateTime, ForeignKey
from typing import Dict, Any
from db_models.db_user import Base

class TokenDbModel(Base):
    """
    Модель таблоицы для подтверждения почты.
    Соответствует структуре: email, token.
    """
    __tablename__ = "user_mail_confirmations"

    # В этой таблице email уникален для каждой записи подтверждения
    email = Column(String, primary_key=True)

    # Сам проверочный код
    token = Column(String)

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование модели в словарь для удобства отладки.
        """
        return {
            "email": self.email,
            "token": self.token,
        }

    def __repr__(self):
        return f"<MailToken(email='{self.email}', token='{self.token[:8]}...')>"