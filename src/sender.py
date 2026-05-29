import pandas as pd
import paho.mqtt.client as mqtt
import json
import time
import os
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()
running = True

def on_message(client, userdata, msg):
    global running
    command = msg.payload.decode()
    if command == "EMERGENCY_STOP":
        logger.critical("EMERGENCY STOP RECEIVED — alert logged, continuing stream for monitoring")
        
#setup
logger.info("Loading env variables...")
broker = os.getenv('MQTT_BROKER')
port = int(os.getenv("MQTT_PORT"))
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
topic = "machine/sensor_data"
#loading dataset
df = pd.read_csv('data/ai4i2020.csv')
_, df_test = train_test_split(df, test_size=0.2, random_state=42)
df_test = df_test.reset_index(drop=True)
#mqtt_setup
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="sender_01")
client.username_pw_set(username,password)
client.on_message = on_message
client.tls_set()
client.connect(broker,port)
logger.info("Connected!")
client.loop_start()
client.subscribe("machine/command")
for index, row in df_test.iterrows():
    if not running:
        break

    logger.info(f"Sent row {index + 1}/{len(df_test)} | RPM: {row['Rotational speed [rpm]']} | Failure: {int(row['Machine failure'])}")
    payload = {
        'udi' : int(row['UDI']),
        'type' : row['Type'],
        'air_temp' : row['Air temperature [K]'],
        'process_temp' : row['Process temperature [K]'],
        'rpm' : row['Rotational speed [rpm]'],
        'torque' : row['Torque [Nm]'],
        'tool_wear' : row['Tool wear [min]'],
        'actual_failure' : int(row['Machine failure'])
    }

    client.publish(topic, json.dumps(payload))
    time.sleep(1)

client.loop_stop()
client.disconnect()
logger.info("MQTT disconnected. Sender shut down.")