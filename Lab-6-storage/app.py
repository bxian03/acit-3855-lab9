import connexion
from connexion import NoContent

from sqlalchemy import create_engine, and_
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
import time

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, "r") as fp:
    app_config = yaml.safe_load(fp.read())

with open(log_conf_file, "r") as fp:
    log_config = yaml.safe_load(fp.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

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

def get_pizza_order(start_timestamp: str, end_timestamp: str):
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    orders = session.query(PizzaOrder).filter(
        and_(
            PizzaOrder.time_created >= start_timestamp_datetime,
            PizzaOrder.time_created < end_timestamp_datetime)
    )

    results_list = []

    for order in orders:
        results_list.append(order.to_dict())

    session.close()

    logger.info(
        f"Query for pizza orders returned after {start_timestamp} returns {len(results_list)} results"
    )

    return results_list, 200

def get_driver_order(start_timestamp:str,end_timestamp:str):
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    orders = session.query(DriverOrder).filter(
        and_(
            DriverOrder.time_created >= start_timestamp_datetime,
            DriverOrder.time_created < end_timestamp_datetime
        )
    )

    results_list = []

    for order in orders:
        results_list.append(order.to_dict())

    session.close()

    logger.info(
        f"Query for driver orders returned after {start_timestamp} returns {len(results_list)} results"
    )

    return results_list, 200


def process_messages():
    """Process event messages"""
    hostname = "%s:%d" % (
        app_config["events"]["hostname"],
        app_config["events"]["port"],
    )
    retries = 0
    while retries <= app_config["events"]["retries"]:
        try:
            logger.info("Connecting to Kafka...")
            if retries > 0:
                logger.info(f"Retried {retries} times")
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            logger.info("Successfully connected to Kafka")
            retries = app_config["events"]["retries"]
            break
        except:
            logger.error("Failed to connect to Kafka. Retrying...")
            time.sleep(app_config["events"]["timeout"])
            retries += 1
            


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

