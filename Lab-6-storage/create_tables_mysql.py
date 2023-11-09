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

query = ("""
    CREATE TABLE pizza_order(
        id INT NOT NULL AUTO_INCREMENT,
        pizza_id VARCHAR(250) NOT NULL,
        pizza_sauce VARCHAR(250) NOT NULL,
        pizza_cheese VARCHAR(250) NOT NULL,
        pizza_toppings VARCHAR(250) NOT NULL,
        pizza_cost FLOAT NOT NULL,
        pizza_quantity INT NOT NULL,
        time_created VARCHAR(100) NOT NULL,
        trace_id VARCHAR(100) NOT NULL,
        CONSTRAINT pizza_order_pk PRIMARY KEY (id)
    )
""")
         
query2 = (
    """
    CREATE TABLE driver_order(
        id INT NOT NULL AUTO_INCREMENT, 
        order_id VARCHAR(250) NOT NULL,
        customer_id VARCHAR(250) NOT NULL,
        customer_address VARCHAR(250) NOT NULL,
        order_cost FLOAT NOT NULL,
        pizza_quantity INT NOT NULL,
        time_created VARCHAR(100) NOT NULL,
        trace_id VARCHAR(100) NOT NULL,
        CONSTRAINT  driver_order_pk PRIMARY KEY (id)
    )
    """
)

cursor.execute(query)
cursor.execute(query2)

cursor.close()

db.commit()
db.close()
