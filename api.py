from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from trading_exchange import Exchange, InsufficientFundsException
from matching_engine import Side
import db
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc
import json
import os


def order_book(request, limit=100):
    with db.with_session(request.registry.Session) as session:
        buys = session.query(db.Order).filter_by(side=Side.BUY).order_by(db.Order.price.desc())
        sells = session.query(db.Order).filter_by(side=Side.SELL).order_by(db.Order.price.asc())

        return {
            "buys": list(order.to_public_dict() for order in buys),
            "sells": list(order.to_public_dict() for order in sells),
        }


def status(request):
    with db.with_session(request.registry.Session) as session:
        user = session.query(db.User).get(int(request.matchdict["user"]))

        if user:
            return {
                "user": user.id,
                "fiat": float(user.fiat),
                "btc": float(user.btc),
                "orders": list(order.to_dict() for order in user.orders)
            }
        else:
            request.response.status = 400
            return {"error": "User does not exists."}


def place_order(request):
    with db.with_session(request.registry.Session) as session:
        user = session.query(db.User).get(int(request.matchdict["user"]))
        data = json.loads(request.body)

        exchange = request.registry.exchange
        side = None
        if data["side"] == "BUY":
            side = Side.BUY
        elif data["side"] == "SELL":
            side = Side.SELL
        else:
            request.response.status = 400
            return {"error": "Bad order."}

        try:
            order_id = exchange.place_order(
                db.Order(quantity=data["quantity"], price=data["price"], side=side, user_id=user.id)
            )

            return {
                "order_id": order_id
            }
        except InsufficientFundsException:
            request.response.status = 400
            return {"error": "Insufficient funds."}


def init_data(session):
    try:
        session.add(db.User(id=1, fiat=100, btc=0))
        session.add(db.User(id=2, btc=100, fiat=0))
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        # data already exists. Skip
        session.rollback()
        pass


def init_db():
    engine = db.get_db(os.environ.get("DB_URL", "sqlite:///foo.db"))
    return sessionmaker(bind=engine)


if __name__ == '__main__':
    with Configurator() as config:
        Session = init_db()

        # Set up initial database on first run.
        init_data(Session())

        config.registry.exchange = Exchange(Session)
        config.registry.Session = Session

        config.add_route('book', '/book')
        config.add_view(order_book, route_name='book', request_method="GET", renderer='json')

        config.add_route('status', '/{user}')
        config.add_view(status, route_name='status', request_method="GET", renderer='json')

        config.add_route('place_order', '/{user}/order')
        config.add_view(place_order, route_name='place_order', request_method="POST", renderer='json')

        app = config.make_wsgi_app()
    port = int(os.environ.get("PORT", "6543"))
    server = make_server('0.0.0.0', port, app)
    print(f"Listening on 0.0.0.0:{port}")
    server.serve_forever()
