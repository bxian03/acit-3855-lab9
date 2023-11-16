import connexion
import json
import datetime
import os
import requests
import yaml
import logging
import logging.config
import uuid
import time
from pykafka import KafkaClient
from pykafka.exceptions import SocketDisconnectedError, LeaderNotAvailable

from connexion import NoContent

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

MAX_EVENTS = 10
EVENT_FILE = "./events.json"
URL1 = app_config["eventstore1"]["url"]
URL2 = app_config["eventstore2"]["url"]
KAFKA_SERVER = app_config["events"]["hostname"]
KAKFA_PORT = app_config["events"]["port"]
KAFKA_TOPIC = app_config["events"]["topic"]

with open("log_conf.yml", "r") as fp:
    log_config = yaml.safe_load(fp.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

def kafka_connection():
    retries = 0
    while retries <= app_config["events"]["retries"]:
        try:
            logger.info("Connecting to Kafka...")
            if retries > 0:
                logger.info(f"Retried {retries} times")
            client = KafkaClient(hosts=f"{KAFKA_SERVER}:{KAKFA_PORT}")
            topic = client.topics[str.encode(KAFKA_TOPIC)]
            logger.info("Successfully connected to Kafka")
            retries = app_config["events"]["retries"]
            return topic.get_sync_producer()
            break
        except:
            logger.error("Failed to connect to Kafka. Retrying...")
            time.sleep(app_config["events"]["timeout"])
            retries += 1

def write_log(
    event_name: str, event_type: str, response_code: int = None, trace_id: str = None
) -> uuid.UUID:
    # create the trace id if it doesn't exist
    if trace_id is None:
        trace_id = uuid.uuid4()
    # create the log message
    if event_type == "request":
        log = f"Received event {event_name} request with trace id of {trace_id}"
    elif event_type == "response" and response_code is not None:
        log = f"Returned event {event_name} status {response_code} with trice id of {trace_id}"
    # write the message to console
    logger.info(log)

    return trace_id


def upload_pizza_order(body):
    trace_id = write_log("pizza order", "request")
    body["trace_id"] = str(trace_id)

    # response = requests.post(URL1, headers=headers, json=body)
    # client = KafkaClient(hosts=f"{KAFKA_SERVER}:{KAKFA_PORT}")
    # topic = client.topics[str.encode(KAFKA_TOPIC)]
    # producer = ktopic.get_sync_producer()
    msg = {
        "type": "pizza_order",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body,
    }
    msg_str = json.dumps(msg)
    try:
        producer.produce(msg_str.encode("utf-8"))
    except(SocketDisconnectedError, LeaderNotAvailable) as e:
        logger.error(e)
        # producer = ktopic.get_sync_producer()
        producer.stop()
        producer.start()
        producer.produce(msg_str.encode("utf-8"))

    write_log("pizza order", "response", 201, trace_id)

    return NoContent, 201


def upload_driver_order(body):
    trace_id = write_log("driver order", "request")
    body["trace_id"] = str(trace_id)

    # client = KafkaClient(hosts=f"{KAFKA_SERVER}:{KAKFA_PORT}")
    # topic = client.topics[str.encode(KAFKA_TOPIC)]
    # producer = ktopic.get_sync_producer()

    msg = {
        "type": "driver_order",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body,
    }
    msg_str = json.dumps(msg)
    try:
        producer.produce(msg_str.encode("utf-8"))
    except(SocketDisconnectedError, LeaderNotAvailable) as e:
        logger.error(e)
        # producer = ktopic.get_sync_producer()
        producer.stop()
        producer.start()
        producer.produce(msg_str.encode("utf-8"))
        
    write_log("driver order", "response", 201, trace_id)

    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)
# global producer
producer = kafka_connection()

if __name__ == "__main__":
    app.run(port=8080, debug=True)
