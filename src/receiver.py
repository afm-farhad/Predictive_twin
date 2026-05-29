import paho.mqtt.client as mqtt
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
from dotenv import load_dotenv

load_dotenv()
import logging
logging.basicConfig(
    level = logging.INFO ,
    format = "%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

#setup
logger.info("Loading env variables...")
broker = os.getenv('MQTT_BROKER')
port = int(os.getenv("MQTT_PORT"))
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
topic = "machine/sensor_data"

#influxdb config

influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com"
influx_token = os.getenv('INFLUXDB_TOKEN')
influx_org = os.getenv('INFLUXDB_ORG')
influx_bucket = os.getenv('INFLUXDB_BUCKET')

#influxdb_client

db_client = influxdb_client.InfluxDBClient(
    url = influx_url,
    token = influx_token,
    org = influx_org
)

write_api = db_client.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected to HiveMQ! Reason: {reason_code}")
    client.subscribe(topic)
    logger.info(f"Subscribed to {topic}")
#receiving data

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        logger.info(f"Received | UDI: {data['udi']} | RPM: {data['rpm']} | Failure: {data['actual_failure']}")
        
        point = influxdb_client.Point("machine_telemetry") \
            .tag("type", data["type"]) \
            .tag("udi", str(data["udi"])) \
            .field("air_temp", data["air_temp"]) \
            .field("process_temp", data["process_temp"]) \
            .field("rpm", data["rpm"]) \
            .field("torque", data["torque"]) \
            .field("tool_wear", data["tool_wear"]) \
            .field("actual_failure", data["actual_failure"])

        write_api.write(bucket=influx_bucket, org=influx_org, record=point)
        logger.info("Written to InfluxDB")
    except Exception as e:
        logger.error(f"Error: {e}")



#mqtt_setup
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="receiver_01")
client.username_pw_set(username=username, password=password)
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)
client.loop_forever()