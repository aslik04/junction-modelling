# backend/globals.py

"""

"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "static")

simulation_running = True
simulationTime = 0
lastUpdateTime = None

connected_clients = []

simulationSpeedMultiplier = 1.0
junction_data = None

# Metrics
max_wait_time_n = 0
max_wait_time_s = 0
max_wait_time_e = 0
max_wait_time_w = 0

total_wait_time_n = 0
total_wait_time_s = 0
total_wait_time_e = 0
total_wait_time_w = 0

wait_count_n = 0
wait_count_s = 0
wait_count_e = 0
wait_count_w = 0

max_queue_length_n = 0
max_queue_length_s = 0
max_queue_length_e = 0
max_queue_length_w = 0

spawnRates = {}
junctionSettings = {}
trafficLightSettings = {}
cars = []

db_path = "sqlite:///traffic_junction.db"