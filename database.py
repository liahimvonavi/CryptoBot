from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


DATABASE_URL = "sqlite:///bought_addresses.db"
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

session = Session()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bought_at = Column(DateTime)
    wallet_address = Column(String, nullable=False)
    amount_of_coins = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    invested_amount = Column(Float)
    sold_at = Column(DateTime)
    result = Column(Float)
    already_sold = Column(Boolean, nullable=False, default=False)

Base.metadata.create_all(engine)


def add_transaction_to_db(wallet_address, amount_of_coins, price, invested_amount):
    new_transaction = Transaction(wallet_address=wallet_address, amount_of_coins=amount_of_coins, price=price, invested_amount= invested_amount, already_sold=False, bought_at=datetime.now())
    session.add(new_transaction)
    session.commit()
def delete_transaction(wallet_address):
    transaction = session.query(Transaction).filter_by(wallet_address=wallet_address).first()
    if transaction:
        session.delete(transaction)
        session.commit()
def get_all_transactions():
    return session.query(Transaction).all()
def sold_coin(tx, result):
    tx.already_sold = True
    tx.result = result
    tx.sold_at = datetime.now()
    session.commit()



