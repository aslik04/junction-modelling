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
        server_process = subprocess.Popen([python_executable, "simulation/server.py"], cwd=os.getcwd())
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

def get_session_leaderboard(session_id):
    """Gets the top 10 scores for a specific session."""
    return LeaderboardResult.query.filter_by(session_id=session_id)\
        .order_by(LeaderboardResult.score.desc()).limit(10).all()

def get_all_time_leaderboard():
    """Gets the top 10 scores across all sessions."""
    return LeaderboardResult.query.order_by(LeaderboardResult.score.desc()).limit(10).all()

def save_session_leaderboard_result(session_id, run_id, avg_wait_time,
                                    max_wait_time, max_queue_length, score):
    """Saves a session leaderboard result without deleting older results."""
    result = LeaderboardResult(
        session_id=session_id,
        run_id=run_id,
        avg_wait_time=avg_wait_time,
        max_wait_time=max_wait_time,
        max_queue_length=max_queue_length,
        score=score
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
            "forward": latest_config.north_vph,
            "left": latest_config.north_exit_west_vph,
            "right": latest_config.north_exit_east_vph
        },
        "south": {
            "forward": latest_config.south_vph,
            "left": latest_config.south_exit_west_vph,
            "right": latest_config.south_exit_east_vph
        },
        "east": {
            "forward": latest_config.east_vph,
            "left": latest_config.east_exit_south_vph,
            "right": latest_config.east_exit_north_vph
        },
        "west": {
            "forward": latest_config.west_vph,
            "left": latest_config.west_exit_south_vph,
            "right": latest_config.west_exit_north_vph
        }
    }

# To Process CSV data instead of input text boxes
def process_csv(file):
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)
    configurations = []
    for row in csv_input:
        config = Configuration(
            run_id=row['run_id'],
            # lanes=row['lanes'],
            pedestrian_crossings=str(row['pedestrian_crossings']).strip().lower() == 'true',
            pedestrian_time=row['pedestrian_time'],
            pedestrian_frequency=row['pedestrian_frequency'],
            north_vph=row['north_vph'],
            north_exit_east_vph=row['north_exit_east_vph'],
            north_exit_west_vph=row['north_exit_west_vph'],
            north_exit_south_vph=row['north_exit_south_vph'],
            south_vph=row['south_vph'],
            south_exit_east_vph=row['south_exit_east_vph'],
            south_exit_west_vph=row['south_exit_west_vph'],
            south_exit_north_vph=row['south_exit_north_vph'],
            east_vph=row['east_vph'],
            east_exit_north_vph=row['east_exit_north_vph'],
            east_exit_south_vph=row['east_exit_south_vph'],
            east_exit_west_vph=row['east_exit_west_vph'],
            west_vph=row['west_vph'],
            west_exit_north_vph=row['west_exit_north_vph'],
            west_exit_south_vph=row['west_exit_south_vph'],
            west_exit_east_vph=row['west_exit_east_vph']
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

@app.route('/parameters', methods=['GET', 'POST'])
def parameters():
    if request.method == 'POST':
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
                int(data.get('nb_exiting_east', 0)) +
                int(data.get('nb_exiting_west', 0)) +
                int(data.get('nb_exiting_south', 0))
            )

            south_vph = (
                int(data.get('sb_exiting_north', 0)) +
                int(data.get('sb_exiting_east', 0)) +
                int(data.get('sb_exiting_west', 0))
            )

            east_vph = (
                int(data.get('eb_exiting_north', 0)) +
                int(data.get('eb_exiting_south', 0)) +
                int(data.get('eb_exiting_west', 0))
            )

            west_vph = (
                int(data.get('wb_exiting_north', 0)) +
                int(data.get('wb_exiting_south', 0)) +
                int(data.get('wb_exiting_east', 0))
            )

            # Store user input in the database
            config = Configuration(
                session_id=session.id,

                # Junction Settings
                lanes=int(data.get('lanes', 2)),  
                left_turn_lane=('left-turn' in data),  
                pedestrian_crossings=safe_int(data.get('pedestrian-events', '0')),  

                # Northbound
                north_vph=north_vph,
                north_exit_east_vph=int(data.get('nb_exiting_east', 0)),
                north_exit_south_vph=int(data.get('nb_exiting_south', 0)),
                north_exit_west_vph=int(data.get('nb_exiting_west', 0)),

                # Southbound
                south_vph=south_vph,
                south_exit_north_vph=int(data.get('sb_exiting_north', 0)),
                south_exit_east_vph=int(data.get('sb_exiting_east', 0)),
                south_exit_west_vph=int(data.get('sb_exiting_west', 0)),

                # Eastbound
                east_vph=east_vph,
                east_exit_north_vph=int(data.get('eb_exiting_north', 0)),
                east_exit_south_vph=int(data.get('eb_exiting_south', 0)),
                east_exit_west_vph=int(data.get('eb_exiting_west', 0)),

                # Westbound
                west_vph=west_vph,
                west_exit_north_vph=int(data.get('wb_exiting_north', 0)),
                west_exit_south_vph=int(data.get('wb_exiting_south', 0)),
                west_exit_east_vph=int(data.get('wb_exiting_east', 0))
            )

            db.session.add(config)
            db.session.commit()
            print(f"✅ Data stored with run_id {config.run_id}")

            # Construct the spawn rates dictionary
            spawn_rates = {
                "north": {
                    "forward": int(data.get('nb_exiting_east', 0)),
                    "left": int(data.get('nb_exiting_west', 0)),
                    "right": int(data.get('nb_exiting_south', 0))
                },
                "south": {
                    "forward": int(data.get('sb_exiting_north', 0)),
                    "left": int(data.get('sb_exiting_west', 0)),
                    "right": int(data.get('sb_exiting_east', 0))
                },
                "east": {
                    "forward": int(data.get('eb_exiting_north', 0)),
                    "left": int(data.get('eb_exiting_west', 0)),
                    "right": int(data.get('eb_exiting_south', 0))
                },
                "west": {
                    "forward": int(data.get('wb_exiting_north', 0)),
                    "left": int(data.get('wb_exiting_south', 0)),
                    "right": int(data.get('wb_exiting_east', 0))
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

            return redirect(url_for('junctionPage')) 

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return jsonify({'error': str(e)}), 400

    return render_template('parameters.html')


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
                    pedestrian_crossings='pedestrian_crossings' in data,
                    pedestrian_time=int(data.get('pedestrian_time', 0)),
                    pedestrian_frequency=int(data.get('pedestrian_frequency', 0)),
                    north_vph=int(data.get('north_vph', 0)),
                    north_exit_east_vph=int(data.get('north_exit_east_vph', 0)),
                    north_exit_west_vph=int(data.get('north_exit_west_vph', 0)),
                    north_exit_south_vph=int(data.get('north_exit_south_vph', 0)),
                    south_vph=int(data.get('south_vph', 0)),
                    south_exit_east_vph=int(data.get('south_exit_east_vph', 0)),
                    south_exit_west_vph=int(data.get('south_exit_west_vph', 0)),
                    south_exit_north_vph=int(data.get('south_exit_north_vph', 0)),
                    east_vph=int(data.get('east_vph', 0)),
                    east_exit_north_vph=int(data.get('east_exit_north_vph', 0)),
                    east_exit_south_vph=int(data.get('east_exit_south_vph', 0)),
                    east_exit_west_vph=int(data.get('east_exit_west_vph', 0)),
                    west_vph=int(data.get('west_vph', 0)),
                    west_exit_north_vph=int(data.get('west_exit_north_vph', 0)),
                    west_exit_south_vph=int(data.get('west_exit_south_vph', 0)),
                    west_exit_east_vph=int(data.get('west_exit_east_vph', 0))
                )

                db.session.add(config)
                db.session.commit()  # Save to the database
                print("✅ Data successfully stored in the database.")

            # ✅ Corrected Indentation: Spawn rates dictionary is now **outside** the commit block
            spawn_rates = {
                "north": {
                    "forward": int(data.get('north_vph', 0)),
                    "left": int(data.get('north_exit_west_vph', 0)),
                    "right": int(data.get('north_exit_east_vph', 0))
                },
                "south": {
                    "forward": int(data.get('south_vph', 0)),
                    "left": int(data.get('south_exit_west_vph', 0)),
                    "right": int(data.get('south_exit_east_vph', 0))
                },
                "east": {
                    "forward": int(data.get('east_vph', 0)),
                    "left": int(data.get('east_exit_south_vph', 0)),
                    "right": int(data.get('east_exit_north_vph', 0))
                },
                "west": {
                    "forward": int(data.get('west_vph', 0)),
                    "left": int(data.get('west_exit_south_vph', 0)),
                    "right": int(data.get('west_exit_north_vph', 0))
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
        score = avg_wait_time + (max_wait_time / 2) + (max_queue_length / 5)
        save_session_leaderboard_result(session_id, run_id,
                                        avg_wait_time, max_wait_time,
                                        max_queue_length, score)
        return jsonify({
            'message': 'sim results saved',
            'avg_wait_time': avg_wait_time,
            'max_wait_time': max_wait_time,
            'max_queue_length': max_queue_length,
            'score': score
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/junctionPage')
def junctionPage():
    return render_template('junctionPage.html')

@app.route('/leaderboards')
def leaderboards():
    top_results = get_all_time_leaderboard()
    return render_template('leaderboards.html', results=top_results)

@app.route('/leaderboard/session/<int:session_id>', methods=['GET'])
def session_leaderboard(session_id):
    results = get_session_leaderboard(session_id)
    if not results:
        return jsonify({"message": "no results for this session"}), 200
    return jsonify([r.serialize() for r in results])

@app.route('/leaderboard/all_time', methods=['GET'])
def all_time_leaderboard():
    results = get_all_time_leaderboard()
    if not results:
        return jsonify({"message": "no results found"}), 200
    return jsonify([r.serialize() for r in results])

if __name__ == '__main__':
    app.run(debug=True)
