# This is a simple implementation of a trading exchange.

#### Note: Since exchange is still in beta all trades are free (0 trading fee).

## Instructions
To run the project do.
docker-compose build
docker-compose up

This should start the exchange on localhost:80.

## Design
Design consist of three layers.
1. matching engine is a simple implementation of order matching algorithm.
2. trading exchange wraps matching engine and wraps it with durable storage
and business logic (make sure users have enough balance, etc..). It also makes sure that all
interaction with matching engine is single threaded and that all operations are transactional.
3. HTTP Api layer for interacting with trading exchange.


Api calls:
- GET - `/book`
  Returns the order book.
  """
    {
      "buys": [
        {
          "side": "BUY",
          "price": 3,
          "quantity": 1
        },
      ],
      "sells": [
        {
          "side": "SELL",
          "price": 3.5,
          "quantity": 0.5
        },
      ]
    }
  """
- GET - `/<user_id>`
  Returns user wallet information and open orders.
  """
    {
      "user": 1,
      "fiat": 56.0,
      "btc": 2.5,
      "orders": [
        {
          "order_id": 5,
          "side": "BUY",
          "price": 3,
          "quantity": 3,
          "filled": 2
        },
        {
          "order_id": 6,
          "side": "BUY",
          "price": 3,
          "quantity": 10,
          "filled": 0
        }
      ]
    }
  """

- POST - `/<user_id>/order`
  Creates a market order.
  """
    {
      "side": BUY|SELL,
      "quantity": FLOAT,
      "price": FLOAT
    }
  """

- DELETE - `/<user_id>/order/<order_id>`
  Cancels the order with the given id.