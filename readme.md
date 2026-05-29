Predictive Maintenance Digital Twin
An ML-powered Industrial IoT system that streams real-world sensor data through MQTT, stores it in a time-series database, and uses an XGBoost classifier to predict machine failures in real-time — triggering automated emergency shutdowns when anomalies are detected.
How It Works
The system runs as three independent services:
Sender replays real sensor data from the AI4I 2020 Predictive Maintenance dataset — streaming RPM, torque, temperature, and tool wear readings over MQTT every second.
Receiver subscribes to the MQTT topic, parses incoming JSON payloads, and writes each reading as a structured data point into InfluxDB Cloud.
Controller polls InfluxDB every 3 seconds, feeds the latest sensor reading into a trained XGBoost model, and checks the predicted failure probability against a configurable threshold. If the confidence exceeds the threshold, it logs a structured incident to the database and publishes an emergency stop command over MQTT — gracefully shutting down the sender.
Tech Stack
LayerTechnologyData SourceAI4I 2020 Predictive Maintenance DatasetMessage BrokerHiveMQ Cloud (MQTT over TLS)Time-Series DBInfluxDB CloudML ModelXGBoost (Binary Classification)Analyticsscikit-learn, pandasVisualizationInfluxDB Dashboard, matplotlib, seabornLanguagePython 3.x