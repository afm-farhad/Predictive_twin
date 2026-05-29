import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import pandas as pd
import pickle
import time
import os
from dotenv import load_dotenv

load_dotenv()
import logging
logging.basicConfig(
    level = logging.INFO ,
    format = "%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)
#database__setup
influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com"
influx_token = os.getenv('INFLUXDB_TOKEN')
influx_org = os.getenv('INFLUXDB_ORG')
influx_bucket = os.getenv('INFLUXDB_BUCKET')

db_client = influxdb_client.InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
query_api = db_client.query_api()
write_api = db_client.write_api(write_options=SYNCHRONOUS)

#mqtt_connection
broker = os.getenv('MQTT_BROKER')
port = int(os.getenv('MQTT_PORT'))
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')

mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="controller_01")
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set()
mqtt_client.connect(broker, port)
mqtt_client.loop_start()


#ML_model
with open('ML/model.pkl', 'rb') as f:
    model = pickle.load(f)
logger.info("Model loaded. Controller is online.")

FAILURE_THRESHOLD = 0.6
last_alert_time = 0
COOLDOWN_SECONDS = 30
last_processed_time = None
while True:
    query = f'''
    from(bucket: "{influx_bucket}")
      |> range(start: -10s)
      |> filter(fn: (r) => r._measurement == "machine_telemetry")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 1)
    '''

    result = query_api.query(org=influx_org, query=query)

    for table in result:
        for record in table.records:
            record_time = record.get_time()
            if record_time == last_processed_time:
                continue
            last_processed_time = record_time
            air_temp = record.values.get("air_temp")
            process_temp = record.values.get("process_temp")
            rpm = record.values.get("rpm")
            torque = record.values.get("torque")
            tool_wear = record.values.get("tool_wear")

            features = pd.DataFrame([[air_temp, process_temp, rpm, torque, tool_wear]], columns=[
                'air_temp',
                'process_temp',
                'rpm',
                'torque',
                'tool_wear'
            ])
            failure_prob = model.predict_proba(features)[0][1]
            status = "FAILURE PREDICTED" if failure_prob >= FAILURE_THRESHOLD else "Normal"
            logger.info(f"RPM: {rpm} | Torque: {torque} | Tool Wear: {tool_wear} | Confidence: {failure_prob:.1%} | >> {status}")

            if failure_prob >= FAILURE_THRESHOLD:
                now = time.time()
                if now - last_alert_time > COOLDOWN_SECONDS:
                    logger.critical("ANOMALY DETECTED — FIRING EMERGENCY STOP")

                    point = influxdb_client.Point("system_alerts") \
                        .tag("asset_id", "motor_01") \
                        .field("action_taken", "EMERGENCY STOP EXECUTED") \
                        .field("fault_type", "ML Predicted Failure") \
                        .field("confidence", float(failure_prob)) \
                        .field("rpm", float(rpm)) \
                        .field("torque", float(torque)) \
                        .field("tool_wear", float(tool_wear))

                    write_api.write(bucket=influx_bucket, org=influx_org, record=point)
                    mqtt_client.publish("machine/command", "EMERGENCY_STOP")
                    logger.critical("Emergency stop command sent to sender.")
                    last_alert_time = now
                else:
                    remaining = COOLDOWN_SECONDS - (now - last_alert_time)
                    logger.warning(f"Anomaly detected but cooldown active. {remaining:.0f}s remaining.")

    time.sleep(3)