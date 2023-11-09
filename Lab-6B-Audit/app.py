import connexion
import json
import yaml
import logging
import logging.config
from pykafka import KafkaClient

from connexion import NoContent

from flask_cors import CORS, cross_origin

with open("app_conf.yml", "r") as fp:
    app_config = yaml.safe_load(fp.read())

MAX_EVENTS = 10
EVENT_FILE = "./events.json"
URL1 = app_config["eventstore1"]["url"]
URL2 = app_config["eventstore2"]["url"]
KAFKA_SERVER = app_config["events"]["hostname"]
KAFKA_PORT = app_config["events"]["port"]
KAFKA_TOPIC = app_config["events"]["topic"]

with open("log_conf.yml", "r") as fp:
    log_config = yaml.safe_load(fp.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")


def get_pizza_order(index):
    """Get pizza order in History"""
    hostname = "%s:%d" % (
        app_config["events"]["hostname"],
        app_config["events"]["port"],
    )
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving pizza order at index %d" % index)
    try:
        arr = []
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            msg = json.loads(msg_str)
            # print(msg)
            # Find the event at the index you want and
            # return code 200
            # i.e., return event, 200
            if msg["type"] == "pizza_order":
                arr.append(msg)

        response = arr[index]["payload"]

        return response, 200
                
    except:
        logger.error("No more messages found")
        logger.error("Could not find pizza order at index %d" % index)
    return {"message": "Not Found"}, 404


def get_driver_order(index):
    """Get driver order in History"""
    hostname = "%s:%d" % (
        app_config["events"]["hostname"],
        app_config["events"]["port"],
    )
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000
    )
    logger.info("Retrieving driver order at index %d" % index)
    try:
        arr = []
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            msg = json.loads(msg_str)
            
            # Find the event at the index you want and
            # return code 200
            # i.e., return event, 200
            if msg["type"] == "driver_order":
                arr.append(msg)
        response = arr[index]["payload"]

        return response, 200
    except:
        logger.error("No more messages found")
        logger.error("Could not find driver order at index %d" % index)
    return {"message": "Not Found"}, 404


app = connexion.FlaskApp(__name__, specification_dir="")
CORS(app.app)
app.app.config["CORS_HEADERS"] = 'Content-Type'
app.add_api("openapi.yaml", strict_validation=True, validate_responses=False)

if __name__ == "__main__":
    app.run(port=9000, debug=True)
