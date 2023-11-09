import mysql.connector
import yaml

with open('app_conf.yml', 'r') as fp:
    app_config = yaml.safe_load(fp.read())

HOST = app_config["mysql"]["MYSQL_HOSTNAME"]
USER = app_config["mysql"]["MYSQL_USER"]
PASSWD = app_config["mysql"]["MYSQL_PASSWORD"]
DATABASE = app_config["mysql"]["MYSQL_DATABASE"]


db = mysql.connector.connect(host=HOST, user=USER, password=PASSWD, database=DATABASE)

cursor = db.cursor(buffered=True)

cursor.execute("DROP TABLE IF EXISTS pizza_order;")
cursor.execute("DROP TABLE IF EXISTS driver_order;")

cursor.close()
db.commit()
db.close()