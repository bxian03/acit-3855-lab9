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
# import numpy as np

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

URL = app_config["eventstore"]["url"]

with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

def init_scheduler():
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
            "pizza_mean_cost": 0,
            "pizza_mean_quantity": 0,
            "pizza_count": 0,
            "order_mean_cost": 0,
            "order_mean_quantity": 0,
            "order_count": 0,
            "last_updated": date,
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
            date = data["last_updated"]

    # date = datetime.datetime.now()

    # format the date to the expected format
    # date = datetime.datetime.strftime(date, "%Y-%m-%dT%H:%M:%SZ")

    # grab data for driver orders
    driver_response = requests.get(f"{URL}/drivers/order?start_timestamp={date}&end_timestamp={datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")

    driver_body = driver_response.json()

    if driver_response.status_code == 200:
        logger.info(f"{len(driver_body)} events received")
    else:
        logger.error("Error in request")

    # grab data for pizza orders
    pizza_response = requests.get(f"{URL}/pizza/order?start_timestamp={date}&end_timestamp={datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")

    pizza_body = pizza_response.json()

    if pizza_response.status_code == 200:
        logger.info(f"{len(pizza_body)}events received")

    # pizza order mean price and mean quantity
    pizza_total_cost = 0
    pizza_total_quantity = 0
    # total of the cost and quantity from the request
    for pizza_order in pizza_body:
        pizza_total_cost += pizza_order["pizza_cost"]
        pizza_total_quantity += pizza_order["pizza_quantity"]

    # add the count of the request with the count of the previously processed requests
    total_pizza_count = len(pizza_body) + data["pizza_count"]
    if total_pizza_count != 0:
        pizza_mean_cost = (
            pizza_total_cost + data["pizza_mean_cost"]
        ) / total_pizza_count
        pizza_mean_quantity = (
            pizza_total_quantity + data["pizza_mean_quantity"]
        ) / total_pizza_count
    else:
        pizza_mean_cost = 0
        pizza_mean_quantity = 0

    # total of the cost and quantity from the request
    order_total_cost = 0
    order_total_quantity = 0
    # total of the cost and quantity from the request
    for driver_order in driver_body:
        order_total_cost += driver_order["order_cost"]
        order_total_quantity += driver_order["pizza_quantity"]

    # add the count of the request with the count of the previously processed requests
    total_order_count = len(driver_body) + data["order_count"]
    if total_order_count != 0:
        order_mean_cost = (
            order_total_cost + data["order_mean_cost"]
        ) / total_order_count
        order_mean_quantity = (
            order_total_quantity + data["order_mean_quantity"]
        ) / total_order_count
    else:
        order_mean_cost = 0
        order_mean_quantity = 0

    # create the newly updated data
    data = {
        "pizza_mean_cost": pizza_mean_cost,
        "pizza_mean_quantity": pizza_mean_quantity,
        "pizza_count": total_pizza_count,
        "order_mean_cost": order_mean_cost,
        "order_mean_quantity": order_mean_quantity,
        "order_count": total_order_count,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open(app_config["datastore"]["filename"], "w") as fp:
        # fp.write()
        json.dump(data, fp)

    logger.debug(data)

    # driver order mean cost and mean quantity


def get_stats():
    logger.info("request has started")

    if os.path.isfile(app_config["datastore"]["filename"]) != True:
        logger.error("Statistics do not exist")
        return NoContent, 404

    with open(app_config["datastore"]["filename"], "r") as fp:
        data = json.load(fp)

    logger.debug(data)

    logger.info("Request has completed")

    return data, 200

init_scheduler()


app = connexion.FlaskApp(__name__, specification_dir="")
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", strict_validation=False, validate_responses=True)

if __name__ == "__main__":
    # init_scheduler()
    app.run(port=8100, debug=True)
