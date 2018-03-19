from matching_engine import Matcher, OrderBook, Order, Side, Transaction
import pytest


@pytest.mark.parametrize("order1,order2", [
    (Order("1", Side.BUY, 100, 1), Order("2", Side.SELL, 100, 1)),
    (Order("1", Side.SELL, 100, 1), Order("2", Side.BUY, 100, 1)),
])
def test_matching_engine(order1, order2):
    buys = OrderBook([], side=Side.BUY)
    sells = OrderBook([], side=Side.SELL)
    matcher = Matcher(buys, sells)

    assert sells.empty()
    assert buys.empty()

    order = Order("1", Side.BUY, 100, 1)
    filled, transactions = matcher.place_order(order)

    assert filled == 0
    assert transactions == []

    sell_order = Order("2", Side.SELL, 100, 1)
    filled, transactions = matcher.place_order(sell_order)

    assert sells.empty()
    assert buys.empty()
    assert filled == 1
    assert [Transaction("1", 1, 100)] == transactions


def test_partial_fill_of_orders():
    buys = OrderBook([], side=Side.BUY)
    sells = OrderBook([], side=Side.SELL)
    matcher = Matcher(buys, sells)

    matcher.place_order(Order("1", Side.BUY, 100, 5))

    filled, transactions = matcher.place_order(Order("2", Side.SELL, 100, 1))

    assert sells.empty()
    assert not buys.empty()
    assert [Transaction("1", 1, 100)] == transactions

    filled, transactions = matcher.place_order(Order("3", Side.SELL, 100, 2))

    assert sells.empty()
    assert not buys.empty()
    assert [Transaction("1", 2, 100)] == transactions

    filled, transactions = matcher.place_order(Order("4", Side.SELL, 100, 3))

    assert not sells.empty()
    assert buys.empty()
    assert [Transaction("1", 2, 100)] == transactions
    assert Order("4", Side.SELL, 100, 1) == sells.peek()


def test_fill_sell_orders_from_cheapest_to_most_expensive():
    buys = OrderBook([], side=Side.BUY)
    sells = OrderBook([], side=Side.SELL)
    matcher = Matcher(buys, sells)

    matcher.place_order(Order("1", Side.SELL, 100, 1))
    matcher.place_order(Order("2", Side.SELL, 102, 1))
    matcher.place_order(Order("3", Side.SELL, 103, 1))
    matcher.place_order(Order("4", Side.SELL, 104, 2))

    filled, transactions = matcher.place_order(Order("5", Side.BUY, 105, 10))

    expected = [
        Transaction("1", 1, 100),
        Transaction("2", 1, 102),
        Transaction("3", 1, 103),
        Transaction("4", 2, 104),
    ]

    assert expected == transactions
    assert filled == 5
    assert Order("5", Side.BUY, 105, 5) == buys.peek()


def test_delete_order():
    buys = OrderBook([], side=Side.BUY)
    sells = OrderBook([], side=Side.SELL)
    matcher = Matcher(buys, sells)

    order1 = Order("1", Side.SELL, 100, 1)
    order2 = Order("2", Side.SELL, 102, 1)
    order3 = Order("3", Side.SELL, 103, 1)

    matcher.place_order(order1)
    matcher.place_order(order2)
    matcher.place_order(order3)

    assert order2 == matcher.delete_order("2", Side.SELL)
    assert order3 == matcher.delete_order("3", Side.SELL)
    assert order1 == matcher.delete_order("1", Side.SELL)

    assert sells.empty()


def test_order_in_the_middle():
    buys = OrderBook([], side=Side.BUY)
    sells = OrderBook([], side=Side.SELL)
    matcher = Matcher(buys, sells)

    sell1 = Order("1", Side.SELL, 100, 1)
    sell2 = Order("2", Side.SELL, 103, 1)

    matcher.place_order(sell1)
    matcher.place_order(sell2)

    buy = Order("4", Side.BUY, 101, 1)
    filled, transactions = matcher.place_order(buy)

    assert filled == 1
