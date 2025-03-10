```markdown
# 🚦 Junction Traffic Simulation System

A software solution to **model and analyze** four-way traffic junction efficiency. It features:

- **Two possible traffic-control methods**:  
  1. **Adaptive Algorithm**: Dynamically adjusts signal timing based on queue lengths.  
  2. **User-defined**: Fixed sequence durations for forward/left and right-turn traffic lights.  

- **Pedestrian crossing** logic with optional Puffin Crossings that halt vehicle flow.
- **Detailed metrics**: average and max wait times, max queue length, plus an **overall efficiency score**.
- **Dual-run simulations** (when user traffic is enabled) or **single-run** (if user traffic is disabled).
- **Leaderboards** for best and recent runs, along with algorithm results.

Below is an **expanded overview** of the system, referencing code modules, file structure, and the **traffic algorithms** in detail.

---

## Table of Contents

1. [Introduction](#introduction)  
2. [Key Features](#key-features)  
3. [Project Structure](#project-structure)  
4. [Installation & Setup](#installation--setup)  
5. [Usage Workflow](#usage-workflow)  
6. [Detailed Traffic Algorithms](#detailed-traffic-algorithms)  
   - [Adaptive Algorithm](#adaptive-algorithm)  
   - [User-Defined (Manual) Algorithm](#user-defined-manual-algorithm)  
   - [Results Display Logic](#results-display-logic)  
7. [Scoring Methodology](#scoring-methodology)  
8. [Leaderboards & Session Tracking](#leaderboards--session-tracking)  
9. [Database & Data Storage](#database--data-storage)  
10. [Testing](#testing)  
11. [Future Extensions](#future-extensions)  
12. [License & Credits](#license--credits)

---

## Introduction

The **Junction Traffic Simulation System** aims to help **local councils** (in a fictional scenario) evaluate a single traffic junction’s performance under different conditions. By configuring:
- **Vehicle arrival rates** (forward / left-turn / right-turn) for each cardinal direction (N, E, S, W),
- **Number of lanes** (1–5),
- **Pedestrian crossing** frequency and duration,
- **Traffic signal mode**: either *Adaptive (dynamic)* or *Manual (user-defined)*,

the simulator:
1. Spawns traffic based on rates.
2. Runs either one or **two** consecutive simulations:
   - If **user traffic is disabled**, we **only** run the *Adaptive* algorithm.
   - If **user traffic is enabled**, we do **two runs**:
     1. Using user-defined signal durations,
     2. Using the *Adaptive* algorithm.  
3. Collects performance metrics: wait times, queue lengths, etc.
4. Calculates an **overall efficiency score**.

Ultimately, users can see **which approach** or **which configuration** yields the **lowest** overall score, i.e., the most efficient traffic flow.

---

## Key Features

1. **Two Traffic-Control Methods**  
   - *Adaptive Algorithm*: Real-time queue-based signal durations.  
   - *User-Defined*: The user enters how long green lights should last for forward/left vs. right-turn flow.

2. **Pedestrian Crossings**  
   - Puffin crossing events block all vehicle traffic.  
   - Configurable crossing frequency and duration.

3. **Dual-run vs. Single-run**  
   - If user-defined lights are enabled, the system simulates that scenario *and* the adaptive scenario for direct comparison.

4. **Weighted Efficiency Scoring**  
   - Combines average wait, max wait, and max queue into an overall metric.

5. **Leaderboard & Data Export**  
   - Session-based best runs.  
   - All-time top 10 user configurations.  
   - Ability to search older runs by session & run ID.  
   - Upload/download CSV or JSON parameters for quick testing.

6. **Extensive Test Suite**  
   - `pytest` coverage on core logic: queueing, traffic lights, adaptive controller, etc.

---

## Project Structure

A summary from the `tree /A /F` command:

```
junction-modelling/
├── app.py                # Main Flask orchestrator
├── backend/
│   ├── server.py         # FastAPI + WebSockets for real-time updates
│   └── junction_objects/ # The core simulation modules
│       ├── adaptive_controller.py
│       ├── traffic_light_controller.py
│       ├── traffic_light_state.py
│       ├── vehicle.py
│       ├── vehicle_movement.py
│       └── vehicle_stop_line.py
├── frontend/             # Additional JS for the canvas (e.g. main.js, junction.js)
├── static/
│   ├── css/              # The system’s CSS (parameters.css, results.css, etc.)
│   ├── js/               # JS files used by HTML templates
│   ├── cars/             # Car images (PNGs)
│   └── pedestrian/       # Pedestrian sprite images (PNGs)
├── templates/            # HTML files: index.html, parameters.html, results.html, ...
├── tests/                # test_*.py modules for unit and integration tests
├── models.py             # SQLAlchemy models
├── requirements.txt
├── pytest.ini
└── traffic_junction.db   # SQLite DB file (auto-created on first run)
```

---

## Installation & Setup

1. **Clone the repo**:

   ```bash
   git clone https://github.com/your-user/junction-modelling.git
   cd junction-modelling
   ```

2. **Create a Virtual Environment** (recommended):

   ```bash
   python -m venv env
   source env/bin/activate  # Mac/Linux
   # Windows:
   #   env\Scripts\activate
   ```

3. **Install Python Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Database Creation**:
   - On first run, the Flask app will automatically create `traffic_junction.db`.

---

## Usage Workflow

1. **Start the Flask + FastAPI servers**:

   ```bash
   python app.py
   ```
   - Or run a helper script like `./run.sh` if provided.

2. **Open** <http://127.0.0.1:5000> in your browser:
   - The **Index/Landing** page is displayed.
   - Click **Begin** → Creates or resumes a session, then leads to **Parameters**.

3. **Parameters** page:
   - Enter your **vehicle flow** for each direction (forward/left/right).
   - Adjust **lanes** (1–5) and **pedestrian** crossing details.
   - Decide if you want to **enable user traffic** settings:
     - If **checked**, fill in cycles per hour + green durations for (N/S) forward/left & right, (E/W) forward/left & right.

4. **File Upload** (optional):
   - Drag-and-drop or browse for **JSON/CSV** containing pre-filled traffic parameters.

5. **Start Simulation**:
   - If user traffic is enabled, the system will eventually run **two** simulations:
     1. Manual/Custom durations,
     2. Adaptive/dynamic approach,
   - If disabled, only the *Adaptive/dynamic approach* is run.

6. **Junction Page**:
   - Real-time or accelerated simulation displayed on the `<canvas>`.
   - **Back** button → cancels run (no results).
   - **End** button → triggers final metric calculations.

7. **Results Page**:
   - If user traffic was enabled, see **both** runs: user config vs. adaptive config side by side.
   - If disabled, only adaptive-run metrics are shown.
   - Displays average wait, max wait, max queue, overall score, and the score difference.

---

## Detailed Traffic Algorithms

### Adaptive Algorithm

The **adaptive controller** (`adaptive_controller.py`) measures queue lengths in each direction:
- Functions like `get_vertical_wait_count`, `get_horizontal_wait_count`, etc.  
- **Non-linear green** formula:

  \[
    \text{green duration} = \text{min} + (\text{max} - \text{min}) \times \frac{\text{queue length}}{\text{queue length} + k}
  \]

  *Typically* `min = 2s`, `max = 20s`, `k = 2.0`.  
  We also apply **exponential smoothing** to avoid abrupt changes.

- Pedestrian crossing events will override all signals to **red** for the crossing duration.

### User-Defined (Manual) Algorithm

If **traffic-light-enable** is checked, the user supplies:
- **Traffic Cycles (per hr)** → how many times per hour we repeat the cycle
- **N/S** forward/left green, right-turn green
- **E/W** forward/left green, right-turn green

During the run:
1. The system runs the manual approach for up to ~5 real-time seconds at 10× speed (equivalent to 50 minutes simulation).
2. Then it automatically re-runs with the adaptive approach for the same time, storing metrics for both.

### Results Display Logic

- **If user traffic is disabled**:  
  - **Only** the adaptive results appear: average wait, max wait, max queue, plus overall adaptive score.
- **If user traffic is enabled**:  
  - We show two distinct sets of metrics:
    1. **User** results (the manual approach)
    2. **Adaptive** results  
  - The **score difference** is `(adaptive_score - user_score)`:
    - Green / positive if the user performed worse (score is higher) or negative if user performed better.

---

## Scoring Methodology

For each direction (N, E, S, W), we measure:
1. **Average Wait Time** (`avgWait`)
2. **Maximum Wait Time** (`maxWait`)
3. **Maximum Queue Length** (`maxQueue`)

**Weighted Direction Score**:
```
score_direction = 0.45 * avgWait + 0.20 * maxWait + 0.35 * maxQueue
```

We then consider **traffic volumes** to normalize each direction. Summing up the 4 normalized direction scores yields the final overall score. A lower score → better efficiency.

**Score Difference** = `(Adaptive Score) - (User Score)`

---

## Leaderboards & Session Tracking

1. **Session**:
   - Whenever you click “Begin” from index.html, a session record is created in `traffic_junction.db`.
   - The session remains active until you “End Session” or close the app.

2. **Leaderboards**:
   - **Session Leaderboard**: 
     - Shows your current session’s best user-run result at the top, plus your 9 other most recent manual runs.
   - **Algorithm Session Leaderboard**:
     - Last 10 runs that used the adaptive approach (these happen automatically each time you end a simulation).
   - **All-time Leaderboard**:
     - Top 10 user runs from any session.
   - **Search**:
     - A dedicated page `/search_Algorithm_Runs` to retrieve a run by `(session_id, run_id)`, or to download all runs.

---

## Database & Data Storage

- **SQLite** DB: `traffic_junction.db`
- **SQLAlchemy** models in `models.py`:
  - `Session`: track user sessions.
  - `Configuration`: stores lane count, vph, pedestrian, etc.
  - `TrafficSettings`: user-chosen or default traffic lights.
  - `LeaderboardResult`: user-run stats.
  - `AlgorithmLeaderboardResult`: adaptive-run stats.

**Data Flow**:
1. **Parameters** page → user forms or file upload → saved in `Configuration` & `TrafficSettings`.
2. **Simulation** → the back-end logs queue/wait times → saved to `LeaderboardResult` or `AlgorithmLeaderboardResult`.
3. **Leaderboards** queries these tables to build top-10 lists or session-based lists.

---

## Testing

1. **Run**:

   ```bash
   pytest
   ```

2. **Test Modules** are under `tests/` plus `test_app.py`:
   - `test_adaptive_controller.py` → Non-linear green, queue logic
   - `test_traffic_light_controller.py` → traffic-lights states
   - `test_traffic_light_state.py` → sequencing transitions
   - `test_vehicle.py`, `test_vehicle_movement.py`, `test_vehicle_stop_line.py` → vehicle logic, queue detection
   - `test_app.py` → API endpoints, database integration tests

3. **Continuous Integration**:
   - Optionally integrate with GitHub Actions or other CI to automatically run `pytest`.

---

## Future Extensions

- **Multi-Junction**:
  - Expand from a single intersection to multiple connected intersections.
- **Bus/Cycle Lanes**:
  - Logic placeholders exist but are not fully implemented.
- **Mobile UI**:
  - Curently targeted at desktop browsers; responsive styling could be improved.
- **Adaptive Pedestrian Timings**:
  - Dynamically adjust crossing durations based on real conditions.

---

## License & Credits

- **Author**: Group 33 – *University of Warwick, 2025* (CS261 Project)
- **Credits**:  
  - **Dorset Software** (simulated client brief),  
  - **Open-source** libraries (Flask, FastAPI, SQLAlchemy, etc.).
- See the project’s LICENSE file for usage guidelines.

**Enjoy exploring your junction optimizations!** 
```