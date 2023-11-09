from sqlalchemy import Column, Integer, String, DateTime, Float
from base import Base
import datetime

class DriverOrder(Base):

    __tablename__ = "driver_order"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(250), nullable=False)
    customer_id = Column(String(250), nullable=False)
    time_created = Column(DateTime, nullable=False)
    customer_address = Column(String(250), nullable=False)
    order_cost = Column(Float, nullable=False)
    pizza_quantity = Column(Integer, nullable=False)
    trace_id = Column(String(100), nullable=False)

    def __init__(self, order_id: str, customer_id: str, customer_address: str, order_cost: float, pizza_quantity: int, trace_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.time_created = datetime.datetime.now()
        self.customer_address = customer_address
        self.order_cost = order_cost
        self.pizza_quantity = pizza_quantity
        self.trace_id = trace_id

    def to_dict(self):
        dict = {}
        dict["id"] = self.id
        dict["order_id"] = self.order_id
        dict["customer_id"] = self.customer_id
        dict["time_created"] = self.time_created
        dict["customer_address"] = self.customer_address
        dict["order_cost"] = self.order_cost
        dict["pizza_quantity"] = self.pizza_quantity
        dict["trace_id"] = self.trace_id

        return dict