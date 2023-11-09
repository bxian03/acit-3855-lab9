import connexion
from connexion import NoContent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from pizza_order import PizzaOrder
from drivers_order import DriverOrder
import datetime
import yaml
import logging
import logging.config
import mysql.connector
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread

with open("app_conf.yml", "r") as fp:
    app_config = yaml.safe_load(fp.read())

with open("log_conf.yml", "r") as fp:
    log_config = yaml.safe_load(fp.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

MYSQL_USER = app_config["mysql"]["MYSQL_USER"]
MYSQL_PASSWORD = app_config["mysql"]["MYSQL_PASSWORD"]
MYSQL_HOSTNAME = app_config["mysql"]["MYSQL_HOSTNAME"]
MYSQL_PORT = app_config["mysql"]["MYSQL_PORT"]
MYSQL_DATABASE = app_config["mysql"]["MYSQL_DATABASE"]

# DB_ENGINE = create_engine("sqlite:///readings.sqlite")
logger.info(f"Connecting to DB. Hostname:{MYSQL_HOSTNAME}, Port:{MYSQL_PORT}")
DB_ENGINE = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOSTNAME}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def write_log(event_name: str, trace_id: str):
    log = f"Stored event {event_name} request with a trace id of {trace_id}"

    logger.debug(log)


# def upload_pizza_order(body):
#     # receives pizza order uploads

#     session = DB_SESSION()

#     pizza_order = PizzaOrder(
#         body["pizza_id"],
#         body["pizza_sauce"],
#         body["pizza_cheese"],
#         body["pizza_toppings"],
#         body["pizza_cost"],
#         body["pizza_quantity"],
#         body["trace_id"],
#     )

#     session.add(pizza_order)

#     session.commit()
#     session.close()

#     write_log("pizza order", body["trace_id"])

#     return NoContent, 201


def get_pizza_order(timestamp: str):
    session = DB_SESSION()

    print(timestamp)

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

    orders = session.query(PizzaOrder).filter(
        PizzaOrder.time_created >= timestamp_datetime
    )

    results_list = []

    for order in orders:
        results_list.append(order.to_dict())

    session.close()

    logger.info(
        f"Query for pizza orders returned after {timestamp} returns {len(results_list)} results"
    )

    return results_list, 200


# def upload_driver_order(body):
#     session = DB_SESSION()

#     driver_order = DriverOrder(
#         body["order_id"],
#         body["customer_id"],
#         body["customer_address"],
#         body["order_cost"],
#         body["pizza_quantity"],
#         body["trace_id"],
#     )

#     session.add(driver_order)

#     session.commit()
#     session.close()

#     write_log("driver order", body["trace_id"])

#     return NoContent, 201


def get_driver_order(timestamp):
    session = DB_SESSION()

    print(timestamp)

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

    orders = session.query(DriverOrder).filter(
        DriverOrder.time_created >= timestamp_datetime
    )

    results_list = []

    for order in orders:
        results_list.append(order.to_dict())

    session.close()

    logger.info(
        f"Query for driver orders returned after {timestamp} returns {len(results_list)} results"
    )

    return results_list, 200


def process_messages():
    """Process event messages"""
    hostname = "%s:%d" % (
        app_config["events"]["hostname"],
        app_config["events"]["port"],
    )
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(
        consumer_group=b"event_group",
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST,
    )

    session = DB_SESSION()

    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode("utf-8")
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]
        logger.debug(f"Payload: {payload}")
        logger.debug(f"Event type: {msg['type']}")
        if msg["type"] == "pizza_order":  # Change this to your event type
            # Store the event1 (i.e., the payload) to the DB
            
            pizza_order = PizzaOrder(
                payload["pizza_id"],
                payload["pizza_sauce"],
                payload["pizza_cheese"],
                payload["pizza_toppings"],
                payload["pizza_cost"],
                payload["pizza_quantity"],
                payload["trace_id"],
            )

            session.add(pizza_order)
            session.commit()
            session.close()

        elif msg["type"] == "driver_order":  # Change this to your event type
            # Store the event2 (i.e., the payload) to the DB
            # Commit the new message as being read
            driver_order = DriverOrder(
                payload["order_id"],
                payload["customer_id"],
                payload["customer_address"],
                payload["order_cost"],
                payload["pizza_quantity"],
                payload["trace_id"],
            )

            session.add(driver_order)
            session.commit()
            session.close()

        consumer.commit_offsets()


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yml", strict_validation=False, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090, debug=True)

