from sqlalchemy import Column, Integer, Enum, ForeignKey, Float, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.exc
from contextlib import contextmanager
import matching_engine


Base = declarative_base()


@contextmanager
def with_session(Session):
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_db(url_string):
    engine = create_engine(url_string)
    try:
        Base.metadata.create_all(engine)
    except sqlalchemy.exc.OperationalError:
        # W8 for db to come up
        import time
        time.sleep(10)
        Base.metadata.create_all(engine)
    return engine


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    side = Column(Enum(matching_engine.Side))
    quantity = Column(Float)
    price = Column(Float)
    filled = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="orders")

    def to_matching_engine_order(self):
        return matching_engine.Order(self.id, self.side, self.price, self.quantity)

    def to_dict(self):
        return {
            "order_id": self.id,
            "side": "BUY" if self.side == matching_engine.Side.BUY else "SELL",
            "price": self.price,
            "quantity": self.quantity,
            "filled": self.filled
        }

    def to_public_dict(self):
        return {
            "side": "BUY" if self.side == matching_engine.Side.BUY else "SELL",
            "price": self.price,
            "quantity": self.quantity - self.filled
        }


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    fiat = Column(Float)
    btc = Column(Float)

    orders = relationship("Order")
