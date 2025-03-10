```markdown
# 🚦 Junction Traffic Simulation System

A comprehensive software solution for modeling and analyzing traffic flow efficiency at a single, four-arm junction. Developed under a simulated commercial project brief for local government transport management, this system enables robust testing and comparison of junction configurations to optimize traffic flow, minimize congestion, and reduce emissions.

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
   - [Leaderboard and Session Tracking](#leaderboard-and-session-tracking)
7. [Traffic Simulation Algorithm](#traffic-simulation-algorithm)
8. [Scoring Methodology](#scoring-methodology)
9. [Running the Tests](#running-the-tests)
10. [Error Handling & Troubleshooting](#error-handling--troubleshooting)
11. [Future Extensions](#future-extensions)
12. [License & Acknowledgments](#license--acknowledgments)

---

## Introduction

The **Junction Traffic Simulation System** simulates vehicle flow and calculates efficiency metrics (average wait, maximum wait, queue lengths, etc.) for a single four-way junction. It can run under either:
- **Adaptive (dynamic) traffic lights**: Lights adjust based on real-time queue lengths.
- **Manual (user-defined) traffic lights**: Users specify green durations and cycles directly.

The system:
- Accepts input parameters (vehicles per hour, pedestrian events, lanes).
- Produces metrics to evaluate and compare different junction configurations.
- Stores results in a local SQLite database for easy retrieval, leaderboard comparisons, and historical analysis.

---

## Features

1. **Adaptive Traffic Light Algorithm**  
   - Dynamically adjusts green durations based on real-time queue lengths.

2. **Manual Traffic Light Configurations**  
   - Users can override the adaptive approach to specify custom green durations.

3. **Real-time Simulation & Visualization**  
   - A fast backend simulation with optional real-time front-end updates (via WebSockets).

4. **Pedestrian Modeling**  
   - Puffin crossing logic that halts all vehicle traffic during pedestrian events.

5. **Session & Leaderboard Tracking**  
   - Compares user-defined vs. adaptive runs.  
   - Session leaderboard highlights the best configuration for the active session.  
   - Algorithm leaderboard tracks the most recent runs of the adaptive algorithm.  
   - All-time leaderboard stores top-performing user-defined configurations.

6. **Scoring & Analytics**  
   - Weighted scoring formula that combines average wait, max wait, and max queue length.  
   - Optionally compare user-run results directly against the adaptive approach.

7. **File Upload Support**  
   - Accepts JSON or CSV for quickly loading traffic parameters, reducing manual setup.

8. **Extensive Testing**  
   - `pytest` coverage for controllers, back-end logic, simulation methods, and the Flask app itself.

---

## Project Structure

Below is a high-level summary. Certain folders may contain additional files not listed here.

```
junction-traffic-simulation/
├── backend/
│   ├── server.py                  # FastAPI server for real-time updates & WebSockets
│   ├── ...
│   └── tests/                     # Contains Python test files for backend (pytest)
├── static/
│   ├── css/                       # CSS files for styling
│   ├── js/                        # Frontend JavaScript modules for traffic lights, canvas, etc.
│   ├── images/                    # Image assets (car sprites, logos, etc.)
│   └── ...
├── templates/
│   ├── index.html                 # Landing page
│   ├── parameters.html            # Parameter input page
│   ├── junctionPage.html          # Real-time simulation page
│   ├── results.html               # Results display page
│   ├── leaderboards.html          # All-time leaderboards
│   ├── session_leaderboard.html   # Leaderboard for user’s session
│   ├── algorithm_session_leaderboard.html   # Leaderboard for adaptive algorithm runs
│   ├── search_Algorithm_Runs.html # Search runs by session/run ID
│   └── error.html                 # Error/exception page
├── tests/
│   ├── test_*.py                  # Additional test files (integration, etc.)
├── app.py                         # Main Flask application (HTTP routes, DB, etc.)
├── models.py                      # SQLAlchemy models (Configuration, Session, LeaderboardResult, etc.)
├── requirements.txt               # Python dependencies
├── README.md                      # This documentation
├── pytest.ini                     # Pytest configuration
└── ...
```

---

## Installation & Setup

**Requirements**:
- Python 3.10+  
- Node.js (optional for advanced front-end builds)  
- A modern web browser  

1. **Clone or Download** this repository:

   ```bash
   git clone https://github.com/your-org/junction-traffic-simulation.git
   cd junction-traffic-simulation
   ```

2. **Create and activate a Python virtual environment** (recommended):

   ```bash
   python -m venv env
   source env/bin/activate      # on Unix-based systems
   # or
   env\Scripts\activate         # on Windows
   ```

3. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:  
   Run the app once (or see the “Usage” section for actual steps) to create the `traffic_junction.db` SQLite database.

---

## Usage

1. **Start the Flask/ FastAPI server**:

   ```bash
   python app.py
   # The server starts both the Flask app and can spin up the FastAPI subprocess.
   ```

2. **Visit** `http://127.0.0.1:5000` in your web browser.  
   - **Landing Page**: Click **“Begin”** to create a new session ID and proceed to the **Parameters** input page.

3. **Set up Parameters** in `parameters.html`:  
   - Vehicle rates (forward/left/right turning), lanes, pedestrian frequency, and duration.  
   - Optionally enable custom traffic light configurations.  
   - **Upload** a JSON or CSV file instead of manual entries if desired.

4. **Run Simulation**:  
   - **Start**: Submits your configuration; you’ll be redirected to the **Junction Simulation** page.  
   - **Junction Simulation** page provides a real-time or accelerated simulation.  
     - Speed slider (0.5x to 5x).  
     - **Back**: Cancels the run and returns to parameters (no result is stored).  
     - **End**: Officially ends the simulation and automatically processes the final results (both user-defined and adaptive runs).  

5. **Analyze Results** in `results.html`:  
   - Compares your user-run metrics vs. the adaptive-run metrics.  
   - Provides wait times, queue lengths, and an overall efficiency score.  
   - Shows difference in scoring if you used your custom traffic lights.

6. **Leaderboards** & **Search**:  
   - **Session Leaderboard**: Best run + last 9 runs of the current session.  
   - **Algorithm Session Leaderboard**: Last 10 runs by the adaptive approach.  
   - **Leaderboards**: All-time user top 10.  
   - **Search**: Look up older runs by session ID and run ID.

---

## Key Components & Code Overview

### Backend (Flask + FastAPI)

- **`app.py`**:  
  - Main Flask application that handles HTTP routes (e.g., `/parameters`, `/results`, `/leaderboards`).  
  - Spawns the **FastAPI** subprocess (`backend/server.py`) for real-time WebSocket updates.  
  - Manages session creation, saving configurations, and orchestrating final metrics calculations.

- **`backend/server.py`**:  
  - FastAPI server responsible for WebSocket connections on `/ws`.  
  - Broadcasts real-time simulation data to any connected clients.

### Database (SQLite + SQLAlchemy)

- **`models.py`** defines DB tables:  
  - **`Session`**: Tracks each user session.  
  - **`Configuration`**: Stores input parameters for each run.  
  - **`TrafficSettings`**: If user-defined traffic lights are enabled, records those durations.  
  - **`LeaderboardResult`** / **`AlgorithmLeaderboardResult`**: Stores performance metrics (avg/max wait, queue length) for each run.

- The default DB file is `traffic_junction.db`.  
- On first run, Flask will create all tables automatically under `db.create_all()`.

### Frontend (HTML/CSS/JS)

- **HTML Templates** in `templates/`:
  - `index.html`, `parameters.html`, `junctionPage.html`, `results.html`, `leaderboards.html`, etc.
- **JavaScript** in `static/js/`:
  - `main.js`, `junction.js`, `trafficLights.js`, `pedestrianManager.js`, etc.
  - Real-time updates via WebSockets at `ws://localhost:8000/ws`.  
  - Canvas rendering for junction layout, lane lines, puffin crossings, etc.
- **CSS** in `static/css/`:
  - Provides styling for each page (e.g., `results.css`, `leaderboards.css`).

### Adaptive vs. Manual Traffic Lights

- By default, the system uses an **adaptive approach** that calculates green phases using exponential smoothing of real-time queue lengths.  
- If **manual** mode is enabled, the user specifies:
  - Traffic cycles per hour (how often signals cycle).
  - Green durations for forward/left and right-turn phases (North/South, East/West).  
- The simulator runs **both**:
  - The manual configuration (if enabled).
  - The adaptive approach (always).

### Leaderboard and Session Tracking

- **Leaderboards** store results from previous runs in the DB.  
  - **Session Leaderboard**: You can see your best run of the current session plus the last 9.  
  - **Algorithm Leaderboard**: Tracks the 10 most recent adaptive runs.  
  - **User Top 10**: All-time best user-defined configurations.  
- **Session** ends when you click **End Session** or re-launch the application, but the data persists in the DB for searching or future reference.

---

## Traffic Simulation Algorithm

1. **Queue Detection**  
   - Real-time vehicle queues are measured per direction:  
     - `get_vertical_wait_count()` / `get_horizontal_wait_count()` exclude right-turn vehicles.  
     - `get_vertical_right_wait_count()` / `get_horizontal_right_wait_count()` handle right turns.

2. **Adaptive Timing**  
   - A non-linear formula sets the green duration:  
     \[
       \text{Green} = \text{min} + (\text{max} - \text{min}) \times 
       \frac{\text{queueLength}}{\text{queueLength} + k}
     \]
   - Exponential smoothing factor to avoid abrupt changes.

3. **Manual Timing**  
   - If enabled, a user-defined “traffic cycles per hour” is used to break down the total time.  
   - Durations for forward/left and right-turn are read from user inputs.

4. **Pedestrian Crossings**  
   - Puffin signals turn on for all arms simultaneously.  
   - The system halts vehicle traffic during crossing intervals.

---

## Scoring Methodology

For each direction (N, S, E, W), we measure:

1. **Average Wait Time** (heaviest weight: 45%)  
2. **Maximum Wait Time** (weight: 20%)  
3. **Maximum Queue Length** (weight: 35%)

A direction score is:

\[
 \text{Direction Score} = 0.45 * \text{AvgWait} + 0.2 * \text{MaxWait} + 0.35 * \text{MaxQueue}
\]

By default, the system compares:
- **User’s Score** vs. **Adaptive Score**  
  - “Score Difference” = (Adaptive) - (User)

---

## Running the Tests

This project includes **pytest** test files for both the Flask app and the back-end simulation logic.

1. **Install dev dependencies** (already in `requirements.txt`), then:
   ```bash
   pytest
   ```
   or
   ```bash
   pytest -v  # verbose mode
   ```

2. Test files of note:
   - `test_app.py` – Integration tests for Flask endpoints & DB interactions
   - `test_adaptive_controller.py` – Unit tests for the adaptive traffic logic
   - `test_traffic_light_controller.py` – Tests the traffic light controller logic
   - `test_traffic_light_state.py` – Traffic light state sequence tests
   - `test_vehicle.py`, `test_vehicle_movement.py`, `test_vehicle_stop_line.py` – Vehicle movement and queue logic

3. A `pytest.ini` file is present to filter deprecation warnings and set general pytest config.

---

## Error Handling & Troubleshooting

1. **Dedicated Error Page**  
   - If any required parameters are missing or invalid, or if an exception occurs, the system redirects to `error.html` to display a user-friendly message.

2. **Flask Debug Mode**  
   - In development, you can enable debug mode:
     ```bash
     FLASK_ENV=development python app.py
     ```
   - Provides stack traces in the browser if an unhandled exception occurs.

3. **Database**  
   - Ensure `traffic_junction.db` is not read-only and that your user can write to the project folder.

4. **FastAPI Not Starting**  
   - Check if another process is using port `8000`.  
   - Some OS or firewall might block the port.

5. **WebSocket Fails**  
   - Ensure you’re using `http://127.0.0.1:5000` or `http://localhost:5000` exactly in your browser and not mixing with `https` or different ports.

---

## Future Extensions

1. **Multi-Junction Support**  
   - Expand from single junction to a small network or multi-intersection scenario.

2. **Dynamic Lane Merging**  
   - Enhance realism by modeling merges, partial lanes, or ephemeral bus lanes.

3. **Adaptive Pedestrian Crossings**  
   - More advanced logic for pedestrian events (e.g., button requests).

4. **Mobile Responsiveness**  
   - The front end is primarily sized for desktop; more effort needed for mobile.

5. **Advanced Graphical Effects**  
   - Add car sprites for turning arcs, smoother transitions, or 3D overlays.

---

## License & Acknowledgments

- This system was developed as part of the **CS261 Project 2025** at the University of Warwick in collaboration with **Dorset Software Services**.
- Created by **Group 33**: *Adam Fawaz, Adam Salik, Chinua Imoh, Christian Otu, Nikit Sajiv, Robert Mascarenhas*.
- All code is under [MIT License](./LICENSE) or similar open-source license (if not provided, see your institution’s guidelines).

> **Contact**: For further questions or contributions, please open an issue on this repo or contact the project maintainers.

---
```
