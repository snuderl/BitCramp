from collections import namedtuple
import enum


Transaction = namedtuple("Transaction", ["order_id", "quantity", "price"])


class Side(enum.Enum):
    BUY = 1
    SELL = 2


class Order:
    def __init__(self, order_id, side, price, quantity):
        self.order_id = order_id
        self.side = side
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.order_id}, {self.side}, {self.price}, {self.quantity})"

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False


class OrderBook:
    """
    This class is used to store the orders for either BUY or SELL side of the order book.
    All orders are stored in memory as a sorted list. This results in very fast order matching
    but adding and deleting order is slow O(n).
    """

    def __init__(self, orders, side):
        self.side = side
        self.orders = list(orders)
        self.is_reverse = self.side == Side.SELL
        self._sort(self.orders)

    def _sort(self, orders):
        self.orders = sorted(orders, key=lambda x: x.price, reverse=self.is_reverse)

    def add(self, order):
        assert order.side == self.side
        self.orders.append(order)
        self._sort(self.orders)
        print(self.orders)

    def empty(self):
        return not bool(self.orders)

    def peek(self):
        if not self.empty():
            return self.orders[-1]

    def pop(self, order_id=None):
        if not order_id:
            return self.orders.pop()

        index = next(idx for idx, order in enumerate(self.orders) if order.order_id == order_id)
        return self.orders.pop(index)


class Matcher(object):
    def __init__(self, buys, sells):
        self.buys = buys
        self.sells = sells

    def place_buy_order(self, order):
        sell = self.sells.peek()
        filled = 0
        if sell and order.price >= sell.price:
            fills = []
            while order.price >= sell.price and order.quantity > 0:
                # Use the price of the order already on the books
                price = sell.price
                q = min(sell.quantity, order.quantity)

                order.quantity -= q
                sell.quantity -= q
                filled += q
                fills.append(Transaction(sell.order_id, q, price))

                # If oposite order was fully fulfilied pop it and move to next one
                if sell.quantity == 0:
                    self.sells.pop()
                    sell = self.sells.peek()
                    if not sell:
                        break

            # If order did not get fully filled add it to order book.
            if order.quantity > 0:
                self.buys.add(order)

            return filled, fills
        else:
            self.buys.add(order)
            return filled, []

    def place_sell_order(self, order):
        """ This is basically a copy of the above function and should be merged. """
        buy = self.buys.peek()

        filled = 0
        if buy and order.price <= buy.price:
            fills = []
            while order.price <= buy.price and order.quantity > 0:
                # Use the price of the order already on the books
                price = buy.price
                q = min(buy.quantity, order.quantity)

                order.quantity -= q
                buy.quantity -= q
                filled += q

                fills.append(Transaction(buy.order_id, q, price))

                if buy.quantity == 0:
                    self.buys.pop()
                    buy = self.buys.peek()
                    if not buy:
                        break

            if order.quantity > 0:
                self.sells.add(order)

            return filled, fills
        else:
            self.sells.add(order)
            return filled, []

    def place_order(self, order):
        """
        Add order to the order book and process it.
        Returns - (quantity filled, list of fills)
        """
        if order.side == Side.BUY:
            return self.place_buy_order(order)
        else:
            return self.place_sell_order(order)

    # def is_valid_order(self, order):
    #     if order.side == Side.BUY:
    #         sell = self.sells.peek()
    #         assert order.price >=


    def delete_order(self, order_id, side):
        if side == Side.BUY:
            return self.buys.pop(order_id)
        else:
            return self.sells.pop(order_id)
