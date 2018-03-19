import matching_engine
from threading import Lock
from db import User, Order, with_session


class BaseException(Exception):
    pass


class InsufficientFundsException(BaseException):
    pass


class Exchange(object):
    def __init__(self, Session):
        self.Session = Session
        self._matcher = self._initialize_matching_engine()
        self.lock = Lock()

    def _initialize_matching_engine(self):
        session = self.Session()

        sell, buy = [], []
        for order in session.query(Order).all():
            order = order.to_matching_engine_order()
            if order.side == matching_engine.Side.BUY:
                buy.append(order)
            else:
                sell.append(order)
        sorted(sell, key=lambda x: x.price)
        sorted(buy, key=lambda x: x.price)

        matcher = matching_engine.Matcher(
            matching_engine.OrderBook(buy, matching_engine.Side.BUY),
            matching_engine.OrderBook(sell, matching_engine.Side.SELL),
        )
        return matcher

    def place_order(self, order):
        with self.lock, with_session(self.Session) as session:
            # Preconditions
            user = session.query(User).get(order.user_id)

            has_funds = False
            if order.side == matching_engine.Side.BUY:
                price = order.price * order.quantity
                has_funds = user.fiat >= price
                user.fiat -= price
            else:
                has_funds = user.btc >= order.quantity
                user.btc -= order.quantity

            if not has_funds:
                raise InsufficientFundsException()

            # Required to get the order_id
            session.add(order)
            session.flush()

            filled, fills = self._matcher.place_order(order.to_matching_engine_order())

            order.filled = filled
            for fill in fills:
                other_order = session.query(Order).get(fill.order_id)
                other_user = other_order.user

                # Both users get "money" added to their balances since
                # the order price was substracted when they set the order.
                fiat = fill.price * fill.quantity
                if order.side == matching_engine.Side.BUY:
                    user.btc += fill.quantity
                    other_user.fiat += fiat
                    other_order.filled += fill.quantity
                else:
                    user.fiat += fiat
                    other_user.btc += fill.quantity
                    other_order.filled += fill.quantity

                if other_order.filled == other_order.quantity:
                    session.delete(other_order)

            if order.filled == order.quantity:
                session.delete(order)
            return order.id

    def cancel_order(self, order_id):
        with with_session(self.Session) as session:
            # Make sure order exists before locking
            if not session.query(Order).get(order_id):
                raise BaseException("Order does not exists")

            with self.lock:
                order = session.query(Order).get(order_id)
                session.delete(order)
                self._matcher.delete_order(order_id, order.side)
                user = order.user
                if order.side == matching_engine.Side.BUY:
                    user.fiat += (order.quantity - order.filled) * order.price
                else:
                    user.btc += (order.quantity - order.filled)
