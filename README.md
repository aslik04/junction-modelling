```markdown
# 🚦 Junction Traffic Simulation System

A comprehensive software solution to model and analyze traffic flow efficiency at a **single four-arm junction**. Developed under a simulated commercial project brief, this system enables robust testing of junction configurations for optimized traffic flow, reduced congestion, and lower emissions.

---

## Table of Contents

1. [Introduction](#introduction)  
2. [Features](#features)  
3. [Project Structure](#project-structure)  
4. [Installation & Setup](#installation--setup)  
5. [Usage](#usage)  
6. [Key Components & Code Overview](#key-components--code-overview)  
   - [Backend (Flask + FastAPI)](#backend-flask--fastapi)  
   - [Database (SQLite + SQLAlchemy)](#database-sqlite--sqlalchemy)  
   - [Frontend (HTML/CSS/JS)](#frontend-htmlcssjs)  
   - [Adaptive vs. Manual Traffic Lights](#adaptive-vs-manual-traffic-lights)  
   - [Leaderboards & Session Tracking](#leaderboards--session-tracking)  
7. [Traffic Simulation Algorithm](#traffic-simulation-algorithm)  
8. [Scoring Methodology](#scoring-methodology)  
9. [Test Suite & Continuous Integration](#test-suite--continuous-integration)  
10. [Troubleshooting & Error Handling](#troubleshooting--error-handling)  
11. [Future Extensions](#future-extensions)  
12. [License & Acknowledgments](#license--acknowledgments)

---

## Introduction

The **Junction Traffic Simulation System** models vehicle and pedestrian flow at a **single intersection** with up to four cardinal directions (North, East, South, West). It allows users to configure:
- Vehicle flow rates (forward, left turn, right turn) for each direction.
- Number of lanes (1–5).
- Pedestrian crossing events and durations.
- Optionally, user-defined traffic light sequences vs. a dynamic/adaptive algorithm.

Upon running a simulation, the system collects the following metrics:
- **Average Wait Time** per direction
- **Maximum Wait Time** per direction
- **Maximum Queue Length** per direction
- **Overall Efficiency Score**, comparing user-defined lights vs. dynamic lights

All metrics and configurations are stored in a local **SQLite** database for:
- **Leaderboards** (session-based and all-time)
- **Historical comparisons**
- **Run ID** / **Session ID** lookups

---

## Features

1. **Adaptive Traffic Light Algorithm**  
   - Dynamically adjusts signal timings in real-time based on queue length measurements.

2. **Manual Traffic Configuration**  
   - Users can override adaptive logic by specifying how long green lights stay on for each direction.

3. **Real-time & Accelerated Simulation**  
   - Observe the simulation in real-time via a WebSocket-based update, or run fast calculations in the backend.

4. **Pedestrian Puffin Crossings**  
   - Pedestrian events lock out vehicle flow for designated crossing durations.

5. **Analytics & Scoring**  
   - Weighted scoring system that merges average wait time, max wait time, and max queue length.

6. **Leaderboards & Session Tracking**  
   - Keep track of best user-run results, plus adaptive-run highlights.  
   - Search older runs by session ID and run ID.

7. **Export & Import**  
   - JSON/CSV file uploads for traffic parameters, plus ability to download historical run data.

8. **Comprehensive Test Suite**  
   - `pytest` coverage for controllers, traffic logic, simulation endpoints, etc.

---

## Project Structure

Below is a **detailed tree /A /F** layout of the repository as generated from the CLI:

```
PS C:\Users\aslik\OneDrive\Desktop\junction-modelling> tree /A /F

C:.
|   .DS_Store
|   .gitignore
|   app.py
|   clean.sh
|   junc sim.side
|   models.py
|   parameters.json
|   pytest.ini
|   README.md
|   requirements.txt
|   run.py
|   run.sh
|   setup.sh
|   test_app.py
|   traffic_junction.db
|   
+---backend
|   |   .DS_Store
|   |   server.py
|   |   
|   +---junction_objects
|   |   |   adaptive_controller.py
|   |   |   enums.py
|   |   |   traffic_light_controller.py
|   |   |   traffic_light_state.py
|   |   |   vehicle.py
|   |   |   vehicle_movement.py
|   |   |   vehicle_stop_line.py
|   |   |
|   |   \---__pycache__
|   |           adaptive_controller.cpython-312.pyc
|   |           enums.cpython-312.pyc
|   |           traffic_light_controller.cpython-312.pyc
|   |           traffic_light_state.cpython-312.pyc
|   |           vehicle.cpython-312.pyc
|   |           vehicle_movement.cpython-312.pyc
|   |           vehicle_stop_line.cpython-312.pyc
|   |           __init__.cpython-312.pyc
|   |
|   \---__pycache__
|           app_setup.cpython-312.pyc
|           background_tasks.cpython-312.pyc
|           endpoints.cpython-312.pyc
|           globals.cpython-312.pyc
|           server.cpython-312.pyc
|           simulation.cpython-312.pyc
|           simulation_manager.cpython-312.pyc
|           __init__.cpython-312.pyc
|
+---frontend
|       config.js
|       images.js
|       junction.js
|       main.js
|       pedestrian.js
|       pedestrianManager.js
|       trafficLights.js
|
+---static
|   |   .DS_Store
|   |   dashboard.css
|   |   logo.png
|   |   main.css
|   |
|   +---cars
|   |       blueCar.png
|   |       greenCar.png
|   |       purpleCar.png
|   |       redCar.png
|   |       yellowCar.png
|   |
|   +---css
|   |       algorithm_session_leaderboard.css
|   |       error.css
|   |       index.css
|   |       junctionPage.css
|   |       junction_details.css
|   |       leaderboards.css
|   |       loading.css
|   |       parameters.css
|   |       results.css
|   |       search_Algorithm_Runs.css
|   |       session_leaderboard.css
|   |
|   +---fonts
|   |       SF-Pro.ttf
|   |
|   +---js
|   |       algorithm_session_leaderboard.js
|   |       junctionPage.js
|   |       junction_details.js
|   |       leaderboards.js
|   |       loading.js
|   |       parameters.js
|   |       results.js
|   |       search_Algorithm_Runs.js
|   |       session_leaderboard.js
|   |
|   \---pedestrian
|           start.png
|           walking1.png
|           walking2.png
|
+---templates
|       .DS_Store
|       algorithm_session_leaderboard.html
|       error.html
|       index.html
|       junctionPage.html
|       junction_details.html
|       leaderboards.html
|       loading.html
|       parameters.html
|       results.html
|       search_Algorithm_Runs.html
|       session_leaderboard.html
|
+---tests
|       test_adaptive_controller.py
|       test_traffic_light_controller.py
|       test_traffic_light_state.py
|       test_vehicle.py
|       test_vehicle_movement.py
|       test_vehicle_stop_line.py
|
\---__pycache__
        app.cpython-312.pyc
        models.cpython-312.pyc
```

Key highlights:
- **`app.py`** - Main Flask app orchestrator.
- **`backend/`** - Contains `server.py` (FastAPI + WebSockets) and the `junction_objects/` folder for core simulation logic.
- **`frontend/`** - JavaScript modules for rendering the junction, vehicles, pedestrians, etc.
- **`static/`** - CSS styles, images (car sprites, pedestrian images), and JS for the HTML templates.
- **`templates/`** - HTML pages for the user interface.
- **`tests/`** - Additional Python test files (in addition to `test_app.py`).
- **Database** - `traffic_junction.db` (SQLite file).

---

## Installation & Setup

**Requirements**:
- Python 3.10+
- (Optional) Node.js for advanced front-end tasks
- A modern web browser

1. **Clone / Download** the repository:

   ```bash
   git clone https://github.com/your-github/junction-modelling.git
   cd junction-modelling
   ```

2. **Python Virtual Environment** (recommended):

   ```bash
   python -m venv env
   source env/bin/activate   # Mac/Linux
   # or
   env\Scripts\activate      # Windows
   ```

3. **Install Python Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Database Initialization**:
   - On first run, the Flask app will create `traffic_junction.db` automatically.

---

## Usage

1. **Start the Flask + FastAPI server**:

   ```bash
   python app.py
   # or possibly ./run.sh (if you have a shell script)
   ```

2. **Open** `http://127.0.0.1:5000` in your browser:
   - **Index / Landing** page: click “Begin” to start a new session.

3. **Parameters** (`parameters.html`):
   - Vehicle rates per arm (N, E, S, W).  
   - Lanes (1–5).  
   - Pedestrian crossing frequency & duration.  
   - Optional user traffic lights.

4. **Simulation**:
   - **Start** → Goes to the `junctionPage.html` simulation screen.  
   - **Back** button cancels.  
   - **End** button finalizes run → calculates & displays results in `results.html`.

5. **Analyze**:
   - See user-run vs. adaptive-run metrics side by side.
   - Weighted overall score & difference.

6. **Leaderboards**:
   - **Session** (user’s best and recent runs).
   - **Algorithm** (adaptive’s last 10).
   - **All-time** top user runs.

7. **File Upload**:
   - On the parameters page, you can drop a CSV/JSON to auto-fill traffic data.

---

## Key Components & Code Overview

### Backend (Flask + FastAPI)

- **`app.py`**:
  - Flask routes: `/parameters`, `/results`, `/leaderboards`, etc.
  - Spawns **FastAPI** as a subprocess for real-time simulations.
  - Manages database sessions, stores configurations, calculates final scores.

- **`backend/server.py`**:
  - **FastAPI** application listening on `:8000`.
  - WebSockets for real-time vehicle and traffic updates (`ws://localhost:8000/ws`).
  - Broadcasts queue states, wait times, etc.

### Database (SQLite + SQLAlchemy)

- **`models.py`** includes:
  - **Session** - Tracks each user session start/end.
  - **Configuration** - Records parameters (vph, lanes, etc.).
  - **TrafficSettings** - Stores user-chosen traffic cycles & green durations.
  - **LeaderboardResult** & **AlgorithmLeaderboardResult** for storing metrics.

The database is in `traffic_junction.db` by default. On first run, the app creates all tables automatically (`db.create_all()`).

### Frontend (HTML/CSS/JS)

- **Templates**:  
  - `index.html`, `parameters.html`, `junctionPage.html`, `results.html`, `leaderboards.html`, etc.
- **JavaScript** (in `static/js/` and `frontend/` folder):
  - Real-time updates via `ws://localhost:8000/ws`.
  - Renders the junction, vehicles, traffic lights, and pedestrians on an HTML `<canvas>`.
- **CSS**:  
  - The `static/css/` directory organizes style files for each sub-page or feature.

### Adaptive vs. Manual Traffic Lights

The system can:
1. **Adaptive**: Dynamically calculates green times based on real-time queue counts.
2. **Manual**: User sets traffic cycles per hour & green durations (forward/left vs. right turn).  
**We always compute the adaptive approach** for reference, so you can compare results.

### Leaderboards & Session Tracking

- **Session**:
  - Created upon loading `index.html` → Pressing “Begin” sets a session ID.  
  - Freed on “End Session” or re-init on re-launch.
- **Leaderboards**:
  - **Session Leaderboard**: Shows best user-run of the session + last 9 runs.  
  - **Algorithm Session Leaderboard**: 10 most recent adaptive runs.  
  - **All-time**: Top 10 user configurations across all sessions.

---

## Traffic Simulation Algorithm

1. **Queue Assessment**:  
   - The system measures queue lengths in each direction for forward vs. right-turn lanes (e.g., `get_vertical_wait_count()`, `get_vertical_right_wait_count()`).

2. **Non-linear Timing**:  
   ```
   green = min + (max - min) * (queueLen / (queueLen + k))
   ```
   - Limits abrupt changes via exponential smoothing.

3. **Manual**:  
   - If user-defined, override durations with the specified cycles per hour.

4. **Pedestrian Crossings**:  
   - All directions red for the crossing’s duration.

5. **Simulation**:
   - The system runs either in real-time or at an accelerated factor (e.g., 10× speed for final results).

---

## Scoring Methodology

For each arm (N, E, S, W), we compute:
- **Average Wait** (weight 0.45)
- **Maximum Wait** (weight 0.20)
- **Maximum Queue** (weight 0.35)

**Direction Score**:
```
0.45 * AvgWait + 0.20 * MaxWait + 0.35 * MaxQueue
```

We then sum or compare user-run vs. adaptive-run.  
“Score Difference” = (Adaptive Score) – (User Score).

---

## Test Suite & Continuous Integration

1. **Pytest**:
   - `test_app.py`, plus test files under `/tests/`.
   - `pytest.ini` configures ignoring certain warnings.
   - Run:
     ```bash
     pytest
     ```
2. **Coverage**:
   - Potential to integrate coverage with:
     ```bash
     pytest --cov=.
     ```

3. **Test Modules**:
   - `test_adaptive_controller.py` → adaptive logic
   - `test_traffic_light_controller.py`, `test_traffic_light_state.py` → traffic light transitions
   - `test_vehicle.py`, `test_vehicle_movement.py`, `test_vehicle_stop_line.py` → vehicle queue logic
   - `test_app.py` → Flask endpoints, database integration

---

## Troubleshooting & Error Handling

- **Error Page** (`error.html`):  
  - If a required field is missing or an exception occurs, you’ll see a friendly message.

- **FastAPI Startup Issues**:  
  - Check that port **8000** is free.  
  - Some OS or firewall rules might conflict.

- **WebSockets**:  
  - If real-time updates fail, ensure you’re not mixing `https` with `http`.  
  - `ws://localhost:8000/ws` only works if the server is properly running.

- **Database**:
  - Make sure `traffic_junction.db` is writable.  
  - If you see “OperationalError,” check your file/folder permissions.

---

## Future Extensions

1. **Multi-Junction Modeling**  
   - Expand from a single intersection to a small grid or multiple connected intersections.

2. **Bus/Cycle Lane**  
   - The code placeholders exist, but currently the feature is omitted or disabled by default.

3. **Mobile-Responsive UI**  
   - Currently optimized for desktops; might want to adapt CSS for phones.

4. **Adaptive Pedestrian Timings**  
   - Pedestrian crossing intervals could also become dynamic.

---

## License & Acknowledgments

- **Developed** as part of the **CS261 Project** at **University of Warwick** in collaboration with **Dorset Software Services**.
- **Authors**: Group 33 (Adam Fawaz, Adam Salik, Chinua Imoh, Christian Otu, Nikit Sajiv, Robert Mascarenhas)
- **License**: See [LICENSE file](./LICENSE) (or adapt if needed).
- Many thanks to the open-source community for libraries such as **Flask**, **FastAPI**, **SQLAlchemy**, and **pytest**.

---

**Contact**: For questions or contributions, open an issue or reach out to the maintainers.  
**Happy Simulating!**  
```