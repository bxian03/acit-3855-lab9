import connexion
from connexion import NoContent

import yaml
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime
import requests
import json
from flask_cors import CORS, cross_origin

# set location of conf files
if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

# open the conf files
with open(app_conf_file, "r") as fp:
    app_config = yaml.safe_load(fp.read())

with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
# init the logger
logger = logging.getLogger("basicLogger")
# log the location of conf files
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

# load the variables
URL = app_config["url"]
RECEIVER_PATH = app_config["endpoints"]["receiver"]["path"]
STORAGE_PATH = app_config["endpoints"]["storage"]["path"]
PROCESSING_PATH = app_config["endpoints"]["processing"]["path"]
AUDIT_PATH = app_config["endpoints"]["audit"]["path"]


def init_scheduler():
    """Initialize the scheduler"""
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(
        populate_stats, "interval", seconds=app_config["scheduler"]["period_sec"]
    )
    sched.start()


def populate_stats():
    """Periodically update stats"""
    logger.info("Processing has started")
    # file doesn't exist or file is empty
    if (os.path.isfile(app_config["datastore"]["filename"]) != True) or (
        os.stat(app_config["datastore"]["filename"]).st_size == 0
    ):
        logger.error("file does not exist")
        # # create a default date
        # date = datetime.datetime.fromisoformat("1970-01-01")
        date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        # default data
        data = {
            "receiver": None,
            "storage": None,
            "processing": None,
            "audit": None,
            "last_update": date,
        }
        # recreate the file
        with open(app_config["datastore"]["filename"], "w") as fp:
            json.dump(data, fp)
    # file is not empty
    elif os.stat(app_config["datastore"]["filename"]).st_size != 0:
        # grab the last updated date
        # also grab the last updated values
        ## count of pizzas/orders
        ## averages
        logger.info("Reading previous data")
        with open(app_config["datastore"]["filename"], "r") as fp:
            data = json.load(fp)
            # grab the date
            date = data["last_update"]

    ### Get the status of all end points

    # Try to make a request to the receiver's health end point
    try:
        receiver_response = requests.get(f"http://{URL}/{RECEIVER_PATH}", timeout=5)
        # service is considered up if it replies with 200 OK as expected
        if receiver_response.status_code == 200:
            receiver_health = "Running"
        # in case we get something that isn't 200 OK
        else:
            receiver_health = "NOT OK"
            logger.info("NOT OK")
    # if the request times out (the service is down) the service is considered down
    except:
        receiver_health = "Down"

    # Debug message for receiver health
    logger.debug(f"Receiver: {receiver_health}")

    # Try to make a request to the storage's health end point
    try:
        storge_response = requests.get(f"http://{URL}/{STORAGE_PATH}", timeout=5)
        # service is considered up if it replies with 200 OK as expected
        if storge_response.status_code == 200:
            storage_health = "Running"
        # in case we get something that isn't 200 OK
        else:
            storage_health = "NOT OK"
            logger.info("NOT OK")
    # if the request times out (the service is down) the service is considered down
    except:
        storage_health = "Down"

    # debug message for storage health
    logger.debug(f"Storage: {storage_health}")

    # Try to make a request to processing's health end point
    try:
        processing_response = requests.get(f"http://{URL}/{PROCESSING_PATH}", timeout=5)
        # service is considered up if it replies with 200 OK as expected
        if processing_response.status_code == 200:
            processing_health = "Running"
        # in case we get something that isn't 200 OK
        else:
            processing_health = "NOT OK"
            logger.info("NOT OK")
    # if the request times out (the service is down) the service is considered down
    except:
        processing_health = "Down"

    # debug message for processing health
    logger.debug(f"Processing: {processing_health}")

    # Try to make a request to the audit's health end point
    try:
        audit_response = requests.get(f"http://{URL}/{AUDIT_PATH}", timeout=5)
        # service is considered up if it replies with 200 OK as expected
        if audit_response.status_code == 200:
            audit_health = "Running"
        # in case we get something that isn't 200 OK
        else:
            audit_health = "NOT OK"
            logger.info("NOT OK")
    # if the request times out (the service is down) the service is considered down
    except:
        audit_health = "Down"

    # debug message for audit health
    logger.debug(f"Audit: {audit_health}")

    # format the data
    data = {
        "receiver": receiver_health,
        "storage": storage_health,
        "processing": processing_health,
        "audit": audit_health,
        "last_update": date,
    }
    # write the data to a file
    with open(app_config["datastore"]["filename"], "w") as fp:
        # fp.write()
        json.dump(data, fp)

    # debug the final data
    logger.debug(data)


def health():
    """Return health status of all services"""
    logger.info("request has started")

    # check if the data file exists
    if os.path.isfile(app_config["datastore"]["filename"]) != True:
        logger.error("Statistics do not exist")
        return NoContent, 404

    # read the data file
    with open(app_config["datastore"]["filename"], "r") as fp:
        data = json.load(fp)

    # debug the file
    logger.debug(data)

    # request complete
    logger.info("Request has completed")

    return data, 200


app = connexion.FlaskApp(__name__, specification_dir="")
if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"
app.add_api(
    "openapi.yml",
    base_path="/health",
    strict_validation=True,
    validate_responses=True,
)

if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    init_scheduler()

if __name__ == "__main__":
    app.run(port=8120, use_reloader=False, debug=False)
