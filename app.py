import os
import sys
import time
import subprocess
import csv
import io
import random
import requests
from flask import Flask, request, jsonify, render_template, url_for, redirect, send_from_directory
from models import db, Configuration, LeaderboardResult, Session
from sqlalchemy import inspect

app = Flask(__name__)

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'traffic_junction.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize database, needed os.path to not create db in instance folder
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("Tables created:", inspector.get_table_names())
    print("Database path:", os.path.abspath('traffic_junction.db'))

# ------------------------------------------------------
# Spawn FastAPI (server.py) automatically
# ------------------------------------------------------
server_process = None
def start_fastapi():
    """
    Start the FastAPI server (`server.py`) if it's not already running.
    Adjust 'cwd' if 'server.py' is in a different location.
    """
    global server_process
    if server_process is None or server_process.poll() is not None:
        python_executable = sys.executable
        # Ensure `server.py` runs in the correct folder
        server_dir = os.path.join(os.path.dirname(__file__), "simulation")
        server_script = os.path.join(server_dir, "server.py")
        server_process = subprocess.Popen([python_executable, server_script], cwd=server_dir)
        time.sleep(3)  # Give FastAPI time to start on port 8000
        print("✅ FastAPI server started.")


@app.before_request
def ensure_fastapi_running():
    """
    This runs before handling the first request,
    ensuring FastAPI is running so that ws://localhost:8000/ws is available.
    """
    start_fastapi()

# ------------------------------------------------------
# Serve files from 'frontend' folder (NOT in static/)
# ------------------------------------------------------
@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    """
    Serve files from the 'frontend' folder, which is NOT in /static.
    This lets you use <script src="/frontend/main.js"></script> in your HTML.
    """
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    return send_from_directory(frontend_dir, filename)

def create_session():
    session = Session()
    db.session.add(session)
    db.session.commit()
    return session.id

def end_session(session_id):
    session = Session.query.get(session_id)
    if session:
        session.active = False
        db.session.commit()

# def get_session_leaderboard(session_id):
#     """Gets the top 10 scores for a specific session."""
#     return LeaderboardResult.query.filter_by(session_id=session_id)\
#         .order_by(LeaderboardResult.score.desc()).limit(10).all()

def get_session_leaderboard(session):
    """
    Given a session ID, returns the top 10 LeaderboardResult entries for that session ordered by the calculated total score (ascending).
    """
    # get results that match session ID
    results = LeaderboardResult.query.filter_by(session_id=session).all()
    if not results:
        return []

    # extract metrics for the given session
    avg_wait_times = [r.avg_wait_time for r in results]
    max_wait_times = [r.max_wait_time for r in results]
    max_queue_lengths = [r.max_queue_length for r in results]

    # calculate best (min) and worst (max) values for each metric
    best_avg = min(avg_wait_times)
    worst_avg = max(avg_wait_times)
    best_max_wait = min(max_wait_times)
    worst_max_wait = max(max_wait_times)
    best_max_queue = min(max_queue_lengths)
    worst_max_queue = max(max_queue_lengths)

    def compute_metric_score(x, best, worst):
        """
        Computes the score for a single metric by:
        - S = 100 * (x - best) / (worst - best)
        - Returns 0 if worst == best.
        """
        return 0 if worst == best else 100 * (x - best) / (worst - best)

    # compute total score for each result
    for result in results:
        score_avg = compute_metric_score(result.avg_wait_time, best_avg, worst_avg)
        score_max_wait = compute_metric_score(result.max_wait_time, best_max_wait, worst_max_wait)
        score_max_queue = compute_metric_score(result.max_queue_length, best_max_queue, worst_max_queue)
        total_score = score_avg + score_max_wait + score_max_queue

        # attach the calculated score to the result
        result.calculated_score = total_score

    # sort results by calculated_score in ascending order
    sorted_results = sorted(results, key=lambda r: r.calculated_score)

    # return top 10 results
    return sorted_results[:10]

# def get_all_time_leaderboard():
#     """Gets the top 10 scores across all sessions."""
#     return LeaderboardResult.query.order_by(LeaderboardResult.score.desc()).limit(10).all()

def save_session_leaderboard_result(session_id, run_id, avg_wait_time,
                                    max_wait_time, max_queue_length):
    """Saves a session leaderboard result without deleting older results."""
    result = LeaderboardResult(
        session_id=session_id,
        run_id=run_id,
        avg_wait_time=avg_wait_time,
        max_wait_time=max_wait_time,
        max_queue_length=max_queue_length,
        # score=score
    )
    db.session.add(result)
    db.session.commit()

def get_latest_spawn_rates():
    """
    Retrieves the latest spawn rates from the database.
    """
    latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()

    if not latest_config:
        return {}  # Return empty if no data exists

    return {
        "north": {
            "forward": latest_config.north_forward_vph,
            "left": latest_config.north_left_vph,
            "right": latest_config.north_right_vph
        },
        "south": {
            "forward": latest_config.south_forward_vph,
            "left": latest_config.south_left_vph,
            "right": latest_config.south_right_vph
        },
        "east": {
            "forward": latest_config.east_forward_vph,
            "left": latest_config.east_left_vph,
            "right": latest_config.east_right_vph
        },
        "west": {
            "forward": latest_config.west_forward_vph,
            "left": latest_config.west_left_vph,
            "right": latest_config.west_right_vph
        }
    }

def get_latest_junction_settings():
    """
    Retrieves the latest spawn rates from the database.
    """
    try:
        latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()

        if latest_config:
            return {
                "lanes": latest_config.lanes,
                "left_turn_lane": latest_config.left_turn_lane,
                "bus_lane": latest_config.bus_lane,
                "pedestrian_duration": latest_config.pedestrian_duration,
                "pedestrian_frequency": latest_config.pedestrian_frequency
            }
        else:
            return {
                "lanes": 5,
                "left_turn_lane": False,
                "bus_lane": False,
                "pedestrian_duration": 0,
                "pedestrian_frequency": 0
            }
    except Exception as e:
        print("Error retrieving configuration:", e)
        return {
            "lanes": 5,
            "left_turn_lane": False,
            "bus_lane": False,
            "pedestrian_duration": 0,
            "pedestrian_frequency": 0
        }

# To Process CSV data instead of input text boxes
def process_csv(file):
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)
    configurations = []
    for row in csv_input:
        config = Configuration(
            # lanes=row['lanes'],
            pedestrian_duration=row['pedestrian_duration'],
            pedestrian_frequency=row['pedestrian_frequency'],

            north_forward_vph=row['north_forward_vph'],
            north_left_vph=row['north_left_vph'],
            north_right_vph=row['north_right_vph'],

            south_forward_vph=row['south_forward_vph'],
            south_left_vph=row['south_left_vph'],
            south_right_vph=row['south_right_vph'],

            east_forward_vph=row['east_forward_vph'],
            east_left_vph=row['east_left_vph'],
            east_right_vph=row['east_right_vph'],

            west_forward_vph=row['west_forward_vph'],
            west_left_vph=row['west_left_vph'],
            west_right_vph=row['west_right_vph']
        )
        configurations.append(config)
    return configurations

@app.route('/start_session', methods=['POST'])
def start_session_api():
    session_id = create_session()
    return jsonify({"session_id": session_id, "message": "Session started"})

@app.route('/end_session', methods=['POST'])
def end_session_api():
    session_id = request.json.get('session_id')
    end_session(session_id)
    return jsonify({'message': 'Session ended'})

@app.route('/')
def index():
    session_id = create_session()
    return render_template('index.html', session_id=session_id)

@app.route('/get_session_run_id', methods=['GET'])
def get_session_run_id():
    try:
        # Get the latest active session
        session = Session.query.filter_by(active=True).order_by(Session.id.desc()).first()
        if not session:
            # Create a new session if none exist
            session = Session(active=True)
            db.session.add(session)
            db.session.commit()

        # Get the latest run_id from Configuration
        latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()
        run_id = latest_config.run_id if latest_config else 1  # Default to 1 if no configs exist

        return jsonify({"session_id": session.id, "run_id": run_id})
    
    except Exception as e:
        print(f"❌ Error retrieving session and run_id: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/results')
def results():
    try:
        session_id = request.args.get('session_id', type=int)
        run_id = request.args.get('run_id', type=int)

        if not session_id or not run_id:
            return jsonify({"error": "Missing session_id or run_id"}), 400

        # Generate dummy simulation results
        avg_wait_time = round(random.uniform(5, 20), 2)
        max_wait_time = round(random.uniform(avg_wait_time, 40), 2)
        max_queue_length = random.randint(10, 50)
        #score = round(avg_wait_time + (max_wait_time / 2) + (max_queue_length / 5), 2)

        # Save results to the leaderboard
        save_session_leaderboard_result(session_id, run_id, avg_wait_time, max_wait_time, max_queue_length)

        return render_template(
            'results.html',
            avg_wait_time=avg_wait_time,
            max_wait_time=max_wait_time,
            max_queue_length=max_queue_length,
            #score=score
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/parameters', methods=['GET', 'POST'])
def parameters():
    if request.method == 'POST':
        print("📥 Received Form Data:", request.form)
        try:
            data = request.form  # ✅ Directly use request.form

            print("📥 Received Form Data:", data)  # Debugging

            # Find or create a session
            session = Session.query.filter_by(active=True).first()
            if not session:
                session = Session(active=True)
                db.session.add(session)
                db.session.commit()
            
            def safe_int(value):
                return int(value) if value.strip().isdigit() else 0  # Returns 0 if empty or non-numeric


            # Calculate VPH totals for each direction
            north_vph = (
                int(data.get('nb_forward', 0)) +
                int(data.get('nb_left', 0)) +
                int(data.get('nb_right', 0))
            )

            south_vph = (
                int(data.get('sb_forward', 0)) +
                int(data.get('sb_left', 0)) +
                int(data.get('sb_right', 0))
            )

            east_vph = (
                int(data.get('eb_forward', 0)) +
                int(data.get('eb_left', 0)) +
                int(data.get('eb_right', 0))
            )

            west_vph = (
                int(data.get('wb_forward', 0)) +
                int(data.get('wb_left', 0)) +
                int(data.get('wb_right', 0))
            )

            pedestrian_duration = safe_int(request.form.get('pedestrian-duration', '0'))
            pedestrian_frequency=int(data.get('pedestrian-frequency', 0))

            print(f"🟢 Pedestrian frequency per Hour: {pedestrian_frequency}")
            print(f"🟢 Pedestrian Crossing Duration: {pedestrian_duration} seconds (Type: {type(pedestrian_duration)})")


            # Store user input in the database
            config = Configuration(
                session_id=session.id,

                # Junction Settings
                lanes=int(data.get('lanes', 5)),  
                left_turn_lane=('left-turn' in data),  
                pedestrian_duration=safe_int(data.get('pedestrian-duration', 0)),  # Default 3 seconds
                pedestrian_frequency=int(data.get('pedestrian-frequency', 0)),  # Default 4 frequency per min

                # North
                north_vph=north_vph,
                north_forward_vph=int(data.get('nb_forward', 0)),
                north_left_vph=int(data.get('nb_left', 0)),
                north_right_vph=int(data.get('nb_right', 0)),

                # South
                south_vph=south_vph,
                south_forward_vph=int(data.get('sb_forward', 0)),
                south_left_vph=int(data.get('sb_left', 0)),
                south_right_vph=int(data.get('sb_right', 0)),

                # East
                east_vph=east_vph,
                east_forward_vph=int(data.get('eb_forward', 0)),
                east_left_vph=int(data.get('eb_left', 0)),
                east_right_vph=int(data.get('eb_right', 0)),

                # West
                west_vph=west_vph,
                west_forward_vph=int(data.get('wb_forward', 0)),
                west_left_vph=int(data.get('wb_left', 0)),
                west_right_vph=int(data.get('wb_right', 0))
            )

            db.session.add(config)
            db.session.commit()
            print(f"✅ Data stored with run_id {config.run_id}")

            # Construct the spawn rates dictionary
            spawn_rates = {
                "north": {
                    "forward": int(data.get('nb_forward', 0)),
                    "left": int(data.get('nb_left', 0)),
                    "right": int(data.get('nb_right', 0))
                },
                "south": {
                    "forward": int(data.get('sb_forward', 0)),
                    "left": int(data.get('sb_left', 0)),
                    "right": int(data.get('sb_right', 0))
                },
                "east": {
                    "forward": int(data.get('eb_forward', 0)),
                    "left": int(data.get('eb_left', 0)),
                    "right": int(data.get('eb_right', 0))
                },
                "west": {
                    "forward": int(data.get('wb_forward', 0)),
                    "left": int(data.get('wb_left', 0)),
                    "right": int(data.get('wb_right', 0))
                }
            }

            print("✅ Parsed Spawn Rates:", spawn_rates)  # Debugging

            # Send spawn rates to `server.py`
            try:
                response = requests.post("http://127.0.0.1:8000/update_spawn_rates", json=spawn_rates)
                if response.status_code == 200:
                    print("✅ Spawn rates sent successfully to server.py.")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not reach server.py: {e}")

            # Construct the junction settings dictionary
            junction_settings = {
                "lanes": int(data.get('lanes', 5)),
                "left_turn_lane": 'left-turn' in data,
                "bus_lane": 'bus_lane' in data,
                "pedestrian_duration": safe_int(data.get('pedestrian-duration', 0)),
                "pedestrian_frequency":  safe_int(data.get('pedestrian-frequency', 0)),
            }

            print("✅ Parsed Junction Settings:", junction_settings)  # Debugging

            # Send junction settings to server.py
            try:
                response = requests.post("http://127.0.0.1:8000/update_junction_settings", json=junction_settings)
                if response.status_code == 200:
                    print("✅ Junction settings sent successfully to server.py.")
                else:
                    print(f"❌ Error sending junction settings: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not reach server.py: {e}")

            return redirect(url_for('junctionPage')) 

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return jsonify({'error': str(e)}), 400

    return render_template('parameters.html')


@app.route("/junction_settings_proxy", methods=["GET"])
def junction_settings_proxy():
    # Make an HTTP request from Flask to FastAPI
    try:
        resp = requests.get("http://127.0.0.1:8000/junction_settings")
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload-file', methods=['POST'])
def uploadfile():
    if 'file' not in request.files:
        return "No file part in the request.", 400
    file = request.files['file']
    if file.filename == '':
        return "No file selected.", 400
    # Save or process the file as needed
    return f"File '{file.filename}' uploaded successfully!"

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            if 'file' in request.files:
                file = request.files['file']
                configurations = process_csv(file)
                for config in configurations:
                    db.session.add(config)
                db.session.commit()
                return render_template('success.html', message='parameters saved')
            else:
                data = request.form

                # Store the user input in the database
                config = Configuration(
                    run_id=int(data.get('run_id', 0)),
                    pedestrian_duration=int(data.get('pedestrian_duration', 0)),
                    pedestrian_frequency=int(data.get('pedestrian_frequency', 0)),
                    north_vph=int(data.get('north_vph', 0)),
                    north_forward_vph=int(data.get('north_forward_vph', 0)),
                    north_left_vph=int(data.get('north_left_vph', 0)),
                    north_right_vph=int(data.get('north_right_vph', 0)),
                    south_vph=int(data.get('south_vph', 0)),
                    south_forward_vph=int(data.get('south_forward_vph', 0)),
                    south_left_vph=int(data.get('south_left_vph', 0)),
                    south_right_vph=int(data.get('south_right_vph', 0)),
                    east_vph=int(data.get('east_vph', 0)),
                    east_forward_vph=int(data.get('east_forward_vph', 0)),
                    east_left_vph=int(data.get('east_left_vph', 0)),
                    east_right_vph=int(data.get('east_right_vph', 0)),
                    west_vph=int(data.get('west_vph', 0)),
                    west_forward_vph=int(data.get('west_forward_vph', 0)),
                    west_left_vph=int(data.get('west_left_vph', 0)),
                    west_right_vph=int(data.get('west_right_vph', 0))
                )

                db.session.add(config)
                db.session.commit()  # Save to the database
                print("✅ Data successfully stored in the database.")

            # ✅ Corrected Indentation: Spawn rates dictionary is now **outside** the commit block
            spawn_rates = {
                "north": {
                    "forward": int(data.get('north_forward_vph', 0)),
                    "left": int(data.get('north_left_vph', 0)),
                    "right": int(data.get('north_right_vph', 0))
                },
                "south": {
                    "forward": int(data.get('south_forward_vph', 0)),
                    "left": int(data.get('south_left_vph', 0)),
                    "right": int(data.get('south_right_vph', 0))
                },
                "east": {
                    "forward": int(data.get('east_forward_vph', 0)),
                    "left": int(data.get('east_left_vph', 0)),
                    "right": int(data.get('east_right_vph', 0))
                },
                "west": {
                    "forward": int(data.get('west_forward_vph', 0)),
                    "left": int(data.get('west_left_vph', 0)),
                    "right": int(data.get('west_right_vph', 0))
                }
            }

            print("✅ Form Data Parsed:", spawn_rates)  # Debugging

            # Send this dictionary to `server.py`
            try:
                response = requests.post("http://127.0.0.1:8000/update_spawn_rates", json=spawn_rates)
                if response.status_code == 200:
                    print("✅ Spawn rates sent successfully to server.py.")
                else:
                    print(f"❌ Error sending spawn rates to server.py: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not reach server.py: {e}")

            return render_template('success.html')

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    return render_template('upload.html')


@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        run_id = data.get('run_id')
        session_id = data.get('session_id')
        avg_wait_time = random.uniform(5, 20)
        max_wait_time = random.uniform(avg_wait_time, 40)
        max_queue_length = random.randint(10, 50)
        # score = avg_wait_time + (max_wait_time / 2) + (max_queue_length / 5)
        save_session_leaderboard_result(session_id, run_id,
                                        avg_wait_time, max_wait_time,
                                        max_queue_length)
        return jsonify({
            'message': 'sim results saved',
            'avg_wait_time': avg_wait_time,
            'max_wait_time': max_wait_time,
            'max_queue_length': max_queue_length
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/junctionPage')
def junctionPage():
    return render_template('junctionPage.html')

# @app.route('/leaderboards')
# def leaderboards():
#     top_results = get_all_time_leaderboard()
#     return render_template('leaderboards.html', results=top_results)

@app.route('/leaderboard/session/<int:session_id>', methods=['GET'])
def session_leaderboard(session_id):
    results = get_session_leaderboard(session_id)
    if not results:
        return jsonify({"message": "no results for this session"}), 200
    return jsonify([r.serialize() for r in results])

# @app.route('/leaderboard/all_time', methods=['GET'])
# def all_time_leaderboard():
#     results = get_all_time_leaderboard()
#     if not results:
#         return jsonify({"message": "no results found"}), 200
#     return jsonify([r.serialize() for r in results])


# Route for displaying the session leaderboard page 
@app.route('/session-leaderboard')
def session_leaderboard_page():
    session_id = request.args.get('session_id')  # Getting session ID from query parameter
    results = get_session_leaderboard(session_id)
    return render_template('session_leaderboard.html', results=results)

# Route for displaying the all-time leaderboard page (HTML)
# @app.route('/all-time-leaderboard')
# def all_time_leaderboard_page():
#     results = get_all_time_leaderboard()
#     return render_template('all_time_leaderboard.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
