from sqlalchemy import Column, Integer, String, DateTime, Float
from base import Base
import datetime

class PizzaOrder(Base):
    __tablename__ = "pizza_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pizza_id = Column(String(250), nullable=False)
    time_created = Column(DateTime, nullable=False)
    pizza_sauce = Column(String(250), nullable=False)
    pizza_cheese = Column(String(250), nullable=False)
    pizza_toppings = Column(String(250), nullable=False)
    pizza_cost = Column(Float, nullable=False)
    pizza_quantity = Column(Integer, nullable=False)
    trace_id = Column(String(100), nullable=False)

    def __init__(self, pizza_id: str ,pizza_sauce: str, pizza_chese: str, pizza_toppings: str, pizza_cost: float, pizza_quantity: int, trace_id: str):
        self.pizza_id = pizza_id
        self.time_created = datetime.datetime.now()
        self.pizza_sauce = pizza_sauce
        self.pizza_cheese = pizza_chese
        self.pizza_toppings = pizza_toppings
        self.pizza_cost = pizza_cost
        self.pizza_quantity = pizza_quantity
        self.trace_id = trace_id

    def to_dict(self):
        """Dictionary Representation of a Pizza Order"""
        dict = {}
        dict["id"] = self.id
        dict["pizza_id"] = self.pizza_id
        dict["time_created"]= self.time_created
        dict["pizza_sauce"] = self.pizza_sauce
        dict["pizza_cheese"] = self.pizza_cheese
        dict["pizza_toppings"] = self.pizza_toppings
        dict["pizza_cost"] = self.pizza_cost
        dict["pizza_quantity"] = self.pizza_quantity
        dict["trace_id"] = self.trace_id

        return dict
