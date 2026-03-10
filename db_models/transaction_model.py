from sqlalchemy import Column, String, Integer
#from sqlalchemy.orm import declarative_base, DeclarativeBase
from db_models.db_user import Base


class AccountTransactionTemplate(Base):
    __tablename__ = 'account_transaction_template'
    user = Column(String, primary_key=True)
    balance = Column(Integer, nullable=False)