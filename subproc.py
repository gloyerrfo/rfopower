#!/usr/bin/python3

# subproc
# Subscriber-Processor service on PowerPi
# 1/2/2025  George Loyer
#
# This python program runs as a service and has the function of
# subscribing to MQTT channels running on the mosquitto instance
# on the PowerPi, reading the data published to the MQTT from 
# sensors and other sources, and then processing that data to
# interpret it and to use the needed algorithm to choose an 
# action.
#
# Subscribes to dome indoor temperature and humidity sensor
# channels and to outdoor temperature and humidity sensor channels.
# Uses that data to calculate the dewpoint inside the dome.
#
# Uses the dewpoint calculation and the sensor readings to choose
# between turning a heater on or turning a heater off depending on
# its current state.  Sends the environmental data to a Prometheus
# feed for monitoring with Grafana.
#
# The actions of turning the heater on or off are designed to use
# IFTTT over the internet to control the Alexa-controlled device.


import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge
import requests
import json
import math
import time

# MQTT Configuration
BROKER = "192.168.74.11"  # Replace with your MQTT broker address
PORT = 1883
TOPIC = "dome/data"  # Replace with the MQTT topic for your sensor data

# Constants for dew point calculation
A = 17.27
B = 237.7

# Boltwood III Weather API Configuration
BOLTWOOD_URL = "http://<boltwood-ip>/weather.json"  # Replace with actual URL or local file path
API_TIMEOUT = 5  # seconds

# Prometheus Metrics
mqtt_message_count = Gauge("mqtt_message_count", "Number of MQTT messages received")
indoor_temp_metric = Gauge("indoor_temp", "Current indoor temperature")
indoor_humidity_metric = Gauge("indoor_humidity", "Current indoor humidity")
outdoor_temp_metric = Gauge("outdoor_temp", "Current outdoor temperature")
outdoor_humidity_metric = Gauge("outdoor_humidity", "Current outdoor humidity")

# Thresholds for Actions
DEWPOINT_PLUS = 2.0   # Degrees Celsius above dewpoint temperature to turn heat on
HYSTERESIS = 3.0      # Degrees Celsius above dewpoint + DEWPOINT_PLUS to turn heat off

# IFTTT Configuration
# IFTTT_EVENT_HEAT_ON = "turn_dome_heater_on"
# IFTTT_EVENT_HEAT_OFF = "turn_dome_heater_on"
# IFTTT_KEY = "your_ifttt_webhook_key"

# IFTTT Trigger Function
# def trigger_ifttt(event_name, value1=None, value2=None, value3=None):
#     url = f"https://maker.ifttt.com/trigger/{event_name}/with/key/{IFTTT_KEY}"
#     payload = {"value1": value1, "value2": value2, "value3": value3}
#     response = requests.post(url, json=payload)
#     if response.status_code == 200:
#         print(f"IFTTT Triggered: {event_name} with values {value1}, {value2}, {value3}")
#     else:
#         print(f"Failed to trigger IFTTT: {response.status_code}, {response.text}")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    mqtt_message_count.inc()

    try:
        # Parse the MQTT message payload as JSON
        payload = json.loads(msg.payload.decode())
        indoor_temp = payload.get("temperature")
        indoor_humidity = payload.get("humidity")
        outdoor_temp, outdoor_humidity = get_outdoor_weather_data()

        # Update Prometheus metrics
        if indoor_temp is not None:
            indoor_temp_metric.set(indoor_temp)
        if indoor_humidity is not None:
            indoor_humidity_metric.set(indoor_humidity)
        if outdoor_temp is not None:
            outdoor_temp_metric.set(outdoor_temp)
        if outdoor_humidity is not None:
            outdoor_humidity_metric.set(outdoor_humidity)

        # Check for thresholds and trigger IFTTT
        if control_heater(indoor_temp, outdoor_temp, indoor_humidity):
            trigger_ifttt(IFTTT_EVENT_NAME, value1=f"Heater On")
        else:
            trigger_ifttt(IFTTT_EVENT_NAME, value1=f"Heater Off")

    except Exception as e:
        print(f"Error processing message: {e}")

# Function to calculate dew point
def calculate_dew_point(temp, humidity):
    gamma = (A * temp) / (B + temp) + math.log(humidity / 100.0)
    dew_point = (B * gamma) / (A - gamma)
    return dew_point

# Function to get weather data from Boltwood sensor
def get_outdoor_weather_data():
    # CODE TO USE ASCOM ALPACA LIBRARY: ALPYCA
    return temperature, humidity

# Function to control heater based on conditions
def control_heater(indoor_temp, outdoor_temp, indoor_humidity):
    dew_point = calculate_dew_point(outdoor_temp, indoor_humidity)
    print(f"Indoor Temp: {indoor_temp:.1f}°C, Outdoor Temp: {outdoor_temp:.1f}°C, " f"Dew Point: {dew_point:.1f}°C")
    low_threshold = dew_point + DEWPOINT_PLUS
    high_threshold = dew_point + DEWPOINT_PLUS + HYSTERESIS
    if indoor_temp < low_threshold:  # Keep indoor temp DEWPOINT_PLUS °C above dew point
        print("Turning heater ON at {high_threshold:.1f}ºC")
        return True
    else if indoor_temp > dew_point + DEWPOINT_PLUS + HYSTERESIS: 
        print("Turning heater OFF at {low_threshold:.1f}ºC")
        return False

# Start Prometheus HTTP Server
start_http_server(8001)  # Metrics will be exposed on http://<host>:8000/metrics

# Start MQTT Client
client = mqtt.Client("MQTT_Subscriber")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)

# Run MQTT Client Loop
print("Starting MQTT subscriber...")
client.loop_forever()
