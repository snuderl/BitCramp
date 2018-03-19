import pytest
from matching_engine import Side
from trading_exchange import Exchange
from db import get_db, User, Order


@pytest.fixture
def Session():
    """Session-wide test database."""
    from sqlalchemy.orm import sessionmaker

    engine = get_db("sqlite://")
    return sessionmaker(bind=engine)


@pytest.fixture
def exchange(Session):
    return Exchange(Session)


def test(Session, exchange):
    session = Session()
    user1 = User(id=1, btc=10, fiat=10)
    session.add(user1)
    user2 = User(id=2, btc=10, fiat=10)
    session.add(user2)
    session.commit()

    exchange.place_order(Order(quantity=1, price=0.5, side=Side.BUY, user_id=1))

    assert user1.fiat == 9.5
    assert user1.btc == 10

    exchange.place_order(Order(quantity=1, price=0.5, side=Side.SELL, user_id=2))

    session.refresh(user1)
    session.refresh(user2)

    assert user2.btc == 9
    assert user2.fiat == 10.5

    assert user1.fiat == 9.5
    assert user1.btc == 11


def test_on_different_price_price_of_existing_orders_should_be_used(Session, exchange):
    session = Session()
    user1 = User(id=1, btc=10, fiat=10)
    session.add(user1)
    user2 = User(id=2, btc=10, fiat=10)
    session.add(user2)
    session.commit()

    exchange.place_order(Order(quantity=1, price=0.6, side=Side.BUY, user_id=1))

    assert user1.fiat == 9.4
    assert user1.btc == 10

    exchange.place_order(Order(quantity=1, price=0.4, side=Side.SELL, user_id=2))

    session.refresh(user1)
    session.refresh(user2)

    assert user2.btc == 9
    assert user2.fiat == 10.6

    assert user1.fiat == 9.4
    assert user1.btc == 11


def test_cancel_partially_filled_order(Session, exchange):
    session = Session()
    user1 = User(id=1, btc=10, fiat=10)
    session.add(user1)
    user2 = User(id=2, btc=10, fiat=10)
    session.add(user2)
    session.commit()

    order_id = exchange.place_order(Order(quantity=5, price=1, side=Side.SELL, user_id=1))
    order = session.query(Order).get(order_id)

    assert user1.fiat == 10
    assert user1.btc == 5
    assert order.filled == 0

    exchange.place_order(Order(quantity=3, price=1, side=Side.BUY, user_id=2))

    session.refresh(user1)
    session.refresh(user2)
    session.refresh(order)

    assert user1.fiat == 13
    assert user1.btc == 5

    assert user2.btc == 13
    assert user2.fiat == 7

    assert order.filled == 3

    exchange.cancel_order(order_id)

    session.refresh(user1)
    session.refresh(user2)

    assert user1.fiat == 13
    assert user1.btc == 7
