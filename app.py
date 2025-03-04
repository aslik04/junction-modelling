"""

"""

import os
import sys
import time
import subprocess
import csv
import io
import requests
from flask import Flask, flash, request, jsonify, render_template, url_for, redirect, send_from_directory
from models import db, Configuration, LeaderboardResult, Session, TrafficSettings, AlgorithmLeaderboardResult, AlgorithmTrafficSettings
from sqlalchemy import inspect

app = Flask(__name__)

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'traffic_junction.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    """
    Initialize database and create all tables.
    """
    
    db.create_all()

server_process = None

def start_fastapi():
    """
    Start the FastAPI server as a subprocess.
    
    It provides a small delay to allow the server to initialize.
    
    Global variable 'server_process' is used to track the subprocess.
    """
    
    global server_process
    
    if server_process is None or server_process.poll() is not None:
        python_executable = sys.executable
        # Ensure `server.py` runs in the correct folder
        server_dir = os.path.join(os.path.dirname(__file__), "backend")
        server_script = os.path.join(server_dir, "server.py")
        server_process = subprocess.Popen([python_executable, server_script], cwd=server_dir)
        time.sleep(3)
        print("FastAPI server started.")


def stop_fastapi():
    """
    Stop the running FastAPI server subprocess.
    If the process does not terminate within the timeout,
    it is forcibly killed.
    
    Global variable 'server_process' is used to track and manage the subprocess.
    """
    
    global server_process
    
    if server_process and server_process.poll() is None:  
    
        server_process.terminate()
    
        try:
            server_process.wait(timeout=5) 
        except subprocess.TimeoutExpired:
            server_process.kill()  

        print("FastAPI server stopped.")
        server_process = None

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    """
    API endpoint to start the simulation.
    Returns:
        tuple: A JSON response with a success message and 200 status code.
    """
    
    start_fastapi()
    
    return jsonify({"message": "FastAPI server started"}), 200

@app.route('/stop_simulation', methods=['POST'])
def stop_simulation():
    """
    API endpoint to stop the simulation.
    Returns:
        tuple: A JSON response with a success message and 200 status code.
    """
    
    stop_fastapi()
    
    return jsonify({"message": "FastAPI server stopped"}), 200

@app.route('/back_to_parameters', methods=['GET'])
def back_to_parameters():
    """
    API endpoint to stop the simulation and redirect to parameters page.
    Returns:
        flask.Response: A redirect response to the parameters route.
    """
    
    stop_fastapi()
    
    return redirect(url_for('parameters'))

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    """
    Serve frontend files from the frontend directory.
    
    Args:
        filename (str): The name of the file to be served.
    
    Returns:
        flask.Response: The requested frontend file.
    """
    
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    
    return send_from_directory(frontend_dir, filename)

def create_session():
    """
    Create a new database session for tracking simulations.
    
    Creates a new Session record in the database, commits it, and returns
    the unique session ID.
    
    Returns:
        int: The ID of the newly created session.
    """
    
    session = Session()
    
    db.session.add(session)
    
    db.session.commit()
    
    return session.id

def end_session(session_id):
    """
    Mark a specific session as inactive.
    
    Args:
        session_id (int): The ID of the session to be ended.
    """
    
    session = Session.query.get(session_id)
    
    if session:
        session.active = False
        db.session.commit()

def get_session_leaderboard(session):
    """
    Retrieve and store the leaderboard results for a given session.
    
    Calculates normalised performance scores for leaderboard results 
    Args:
        session (int): The session ID to retrieve leaderboard for.
    
    Returns:
        list: A sorted list of the top 10 leaderboard results.
    """
    results = LeaderboardResult.query.filter_by(session_id=session).all()
    
    if not results:
        return []

    avg_wait_times = [r.avg_wait_time for r in results]
    max_wait_times = [r.max_wait_time for r in results]
    max_queue_lengths = [r.max_queue_length for r in results]

    best_avg = min(avg_wait_times)
    worst_avg = max(avg_wait_times)
    best_max_wait = min(max_wait_times)
    worst_max_wait = max(max_wait_times)
    best_max_queue = min(max_queue_lengths)
    worst_max_queue = max(max_queue_lengths)

    def compute_metric_score(x, best, worst):
        """
        Compute a normalized score for a metric.
        
        Args:
            x (float): The current metric value.
            best (float): The best (lowest) value for the metric.
            worst (float): The worst (highest) value for the metric.
        
        Returns:
            float: A normalized score between 0 and 100.
        """
        
        return 0 if worst == best else 100 * (x - best) / (worst - best)

    for result in results:

        score_avg = compute_metric_score(result.avg_wait_time, best_avg, worst_avg)
        score_max_wait = compute_metric_score(result.max_wait_time, best_max_wait, worst_max_wait)
        score_max_queue = compute_metric_score(result.max_queue_length, best_max_queue, worst_max_queue)
        total_score = score_avg + score_max_wait + score_max_queue
        result.calculated_score = total_score

    sorted_results = sorted(results, key=lambda r: r.calculated_score)
    
    return sorted_results[:10]

def save_session_leaderboard_result(run_id, session_id,
                                  avg_wait_time_n, max_wait_time_n, max_queue_length_n,
                                  avg_wait_time_s, max_wait_time_s, max_queue_length_s, 
                                  avg_wait_time_e, max_wait_time_e, max_queue_length_e,
                                  avg_wait_time_w, max_wait_time_w, max_queue_length_w):
    """
    Save performance metrics for a specific simulation run to the leaderboard.
    
    Args:
        run_id (int): Unique identifier for the simulation run.
        session_id (int): ID of the session associated with the run.
        avg_wait_time_n (float): Average wait time for north-bound traffic.
        max_wait_time_n (float): Maximum wait time for north-bound traffic.
        max_queue_length_n (int): Maximum queue length for north-bound traffic.
        # Similar parameters for south, east, and west directions
    """
    
    result = LeaderboardResult(
        session_id=session_id,
        run_id=run_id,

        avg_wait_time_north=avg_wait_time_n,
        max_wait_time_north=max_wait_time_n, 
        max_queue_length_north=max_queue_length_n,

        avg_wait_time_south=avg_wait_time_s,
        max_wait_time_south=max_wait_time_s,
        max_queue_length_south=max_queue_length_s,

        avg_wait_time_east=avg_wait_time_e,
        max_wait_time_east=max_wait_time_e,
        max_queue_length_east=max_queue_length_e,

        avg_wait_time_west=avg_wait_time_w,
        max_wait_time_west=max_wait_time_w,
        max_queue_length_west=max_queue_length_w
    )

    db.session.add(result)
    db.session.commit()

def save_algorithm_result(run_id, session_id,
                                    avg_wait_time_n, max_wait_time_n, max_queue_length_n,
                                    avg_wait_time_s, max_wait_time_s, max_queue_length_s, 
                                    avg_wait_time_e, max_wait_time_e, max_queue_length_e,
                                    avg_wait_time_w, max_wait_time_w, max_queue_length_w):
    """
    
    """

    result = AlgorithmLeaderboardResult(
        session_id=session_id,
        run_id=run_id,

        avg_wait_time_north=avg_wait_time_n,
        max_wait_time_north=max_wait_time_n, 
        max_queue_length_north=max_queue_length_n,

        avg_wait_time_south=avg_wait_time_s,
        max_wait_time_south=max_wait_time_s,
        max_queue_length_south=max_queue_length_s,

        avg_wait_time_east=avg_wait_time_e,
        max_wait_time_east=max_wait_time_e,
        max_queue_length_east=max_queue_length_e,

        avg_wait_time_west=avg_wait_time_w,
        max_wait_time_west=max_wait_time_w,
        max_queue_length_west=max_queue_length_w
    )

    db.session.add(result)
    db.session.commit()    

def get_latest_spawn_rates():
    """
    Retrieve the latest spawn rates for traffic from the most recent configuration.
    
    Returns:
        dict: A nested dictionary containing spawn rates for each direction 
              and movement type (forward, left, right).
    """
    
    latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()
    
    if not latest_config:
        return {} 
    
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
    Retrieve the latest junction configuration settings.
    
    
    Returns:
        dict: A dictionary containing junction configuration settings 
              like number of lanes, pedestrian settings, etc.
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

def process_csv(file):
    """
    
    """
    
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    
    csv_input = csv.DictReader(stream)
    
    configurations = []
    
    for row in csv_input:
    
        config = Configuration(
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
    """
    
    """
    
    session_id = create_session()
    
    return jsonify({"session_id": session_id, "message": "Session started"})

@app.route('/end_session', methods=['POST'])
def end_session_api():
    """
    
    """
    
    session_id = request.json.get('session_id')
    
    end_session(session_id)
    
    return jsonify({'message': 'Session ended'})

@app.route('/')
def index():
    """
    
    """
    
    session_id = create_session()
    
    return render_template('index.html', session_id=session_id)

@app.route('/index')
def indexTwo():
    """
    
    """

    session_id = create_session()
    
    return render_template('index.html', session_id=session_id)

@app.route('/get_session_run_id', methods=['GET'])
def get_session_run_id():
    """
    
    """
    
    try:

        session = Session.query.filter_by(active=True).order_by(Session.id.desc()).first()
        if not session:

            session = Session(active=True)
            db.session.add(session)
            db.session.commit()


        latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()
        run_id = latest_config.run_id if latest_config else 1  # Default to 1 if no configs exist

        return jsonify({"session_id": session.id, "run_id": run_id})
    
    except Exception as e:
        
        print(f"❌ Error retrieving session and run_id: {e}")
        
        return jsonify({"error": str(e)}), 500


@app.route('/results')
def results():
    """
    
    """
    
    try:
        session_id = request.args.get('session_id', type=int)
        run_id = request.args.get('run_id', type=int)

        if not session_id or not run_id:
            return jsonify({"error": "Missing session_id or run_id"}), 400

        with app.test_request_context(
                '/simulate', 
                method='POST', 
                json={'session_id': session_id, 'run_id': run_id}
            ):
                response = simulate()
                if isinstance(response, tuple):
                    response_data = response[0].json
                else:
                    response_data = response.json

                user_metrics = response_data.get('user', {})

                avg_wait_time_n = user_metrics.get('avg_wait_time_n')
                avg_wait_time_s = user_metrics.get('avg_wait_time_s')
                avg_wait_time_e = user_metrics.get('avg_wait_time_e')
                avg_wait_time_w = user_metrics.get('avg_wait_time_w')

                max_wait_time_n = user_metrics.get('max_wait_time_n')
                max_wait_time_s = user_metrics.get('max_wait_time_s')
                max_wait_time_e = user_metrics.get('max_wait_time_e')
                max_wait_time_w = user_metrics.get('max_wait_time_w')

                max_queue_length_n = user_metrics.get('max_queue_length_n')
                max_queue_length_s = user_metrics.get('max_queue_length_s')
                max_queue_length_e = user_metrics.get('max_queue_length_e')
                max_queue_length_w = user_metrics.get('max_queue_length_w')

                score = user_metrics.get('score')

                default_metrics = response_data.get('default', {})

                algorithm_metrics = {
                    "avg_wait_time_n": default_metrics.get('avg_wait_time_n'),
                    "avg_wait_time_s": default_metrics.get('avg_wait_time_s'),
                    "avg_wait_time_e": default_metrics.get('avg_wait_time_e'),
                    "avg_wait_time_w": default_metrics.get('avg_wait_time_w'),

                    "max_wait_time_n": default_metrics.get('max_wait_time_n'),
                    "max_wait_time_s": default_metrics.get('max_wait_time_s'),
                    "max_wait_time_e": default_metrics.get('max_wait_time_e'),
                    "max_wait_time_w": default_metrics.get('max_wait_time_w'),

                    "max_queue_length_n": default_metrics.get('max_queue_length_n'),
                    "max_queue_length_s": default_metrics.get('max_queue_length_s'),
                    "max_queue_length_e": default_metrics.get('max_queue_length_e'),
                    "max_queue_length_w": default_metrics.get('max_queue_length_w'),

                    "score": default_metrics.get('score')
                }

        spawn_rates = get_latest_spawn_rates()
        junction_settings = get_latest_junction_settings()
        traffic_light_settings = get_latest_traffic_light_settings()

        # Retrieve the default (algorithm) traffic settings from the AlgorithmTrafficSettings table
        default_traffic = AlgorithmTrafficSettings.query.filter_by(session_id=session_id, run_id=run_id).first()
        if default_traffic:
            default_traffic_settings = {
                "enabled": default_traffic.enabled,
                "sequences_per_hour": default_traffic.sequences_per_hour,
                "vertical_main_green": default_traffic.vertical_main_green,
                "horizontal_main_green": default_traffic.horizontal_main_green,
                "vertical_right_green": default_traffic.vertical_right_green,
                "horizontal_right_green": default_traffic.horizontal_right_green,
            }
        else:
            default_traffic_settings = {}

        return render_template(
            'results.html',
            avg_wait_time_n=avg_wait_time_n,
            avg_wait_time_s=avg_wait_time_s,
            avg_wait_time_e=avg_wait_time_e,
            avg_wait_time_w=avg_wait_time_w,
            max_wait_time_n=max_wait_time_n,
            max_wait_time_s=max_wait_time_s,
            max_wait_time_e=max_wait_time_e,
            max_wait_time_w=max_wait_time_w,
            max_queue_length_n=max_queue_length_n,
            max_queue_length_s=max_queue_length_s,
            max_queue_length_e=max_queue_length_e,
            max_queue_length_w=max_queue_length_w,
            score=score,
            spawn_rates=spawn_rates,
            junction_settings=junction_settings,
            traffic_light_settings=traffic_light_settings,
            algorithm_metrics=algorithm_metrics,
            default_traffic_settings=default_traffic_settings
        )

    except Exception as e:        
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 400
    

def get_latest_traffic_light_settings():
    """
    
    """
    
    latest_ts = TrafficSettings.query.order_by(TrafficSettings.id.desc()).first()

    if not latest_ts:

        return {
            "enabled": False,
            "sequences_per_hour": 0,
            "vertical_main_green": 0,
            "horizontal_main_green": 0,
            "vertical_right_green": 0,
            "horizontal_right_green": 0,
        }

    return {
        "enabled": latest_ts.enabled,
        "sequences_per_hour": latest_ts.sequences_per_hour,
        "vertical_main_green": latest_ts.vertical_main_green,
        "horizontal_main_green": latest_ts.horizontal_main_green,
        "vertical_right_green": latest_ts.vertical_right_green,
        "horizontal_right_green": latest_ts.horizontal_right_green,
    }

def get_session_leaderboard_result(session_id, run_id):
    """
    
    """
    
    return LeaderboardResult.query.filter_by(session_id=session_id, run_id=run_id).first()

@app.route('/parameters', methods=['GET', 'POST'])
def parameters():
    """
    
    """
    
    if request.method == 'POST':
    
        print("📥 Received Form Data:", request.form)
    
        try:
            data = request.form 

            print("📥 Received Form Data:", data)

            session = Session.query.filter_by(active=True).first()
            if not session:
                session = Session(active=True)
                db.session.add(session)
                db.session.commit()
            
            def safe_int(value):
                return int(value) if value.strip().isdigit() else 0  

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

            config = Configuration(
                session_id=session.id,

                lanes=int(data.get('lanes', 5)),  
                left_turn_lane=('left-turn' in data),  
                pedestrian_duration=safe_int(data.get('pedestrian-duration', 0)), 
                pedestrian_frequency=int(data.get('pedestrian-frequency', 0)), 

                north_vph=north_vph,
                north_forward_vph=int(data.get('nb_forward', 0)),
                north_left_vph=int(data.get('nb_left', 0)),
                north_right_vph=int(data.get('nb_right', 0)),

                south_vph=south_vph,
                south_forward_vph=int(data.get('sb_forward', 0)),
                south_left_vph=int(data.get('sb_left', 0)),
                south_right_vph=int(data.get('sb_right', 0)),

                east_vph=east_vph,
                east_forward_vph=int(data.get('eb_forward', 0)),
                east_left_vph=int(data.get('eb_left', 0)),
                east_right_vph=int(data.get('eb_right', 0)),

                west_vph=west_vph,
                west_forward_vph=int(data.get('wb_forward', 0)),
                west_left_vph=int(data.get('wb_left', 0)),
                west_right_vph=int(data.get('wb_right', 0))
            )

            db.session.add(config)
            db.session.commit()
            print(f"✅ Data stored with run_id {config.run_id}")

            traffic_enabled = data.get('traffic-light-enable', '') == 'on'
            if traffic_enabled:
                tl_config = TrafficSettings(
                    run_id=config.run_id,
                    session_id=session.id,
                    enabled=True,
                    sequences_per_hour=int(data.get('tl_sequences', 0)),
                    vertical_main_green=int(data.get('tl_vmain', 0)),
                    horizontal_main_green=int(data.get('tl_hmain', 0)),
                    vertical_right_green=int(data.get('tl_vright', 0)),
                    horizontal_right_green=int(data.get('tl_hright', 0))
                )
            else:
                tl_config = TrafficSettings(
                    run_id=config.run_id,
                    session_id=session.id,
                    enabled=False,
                    sequences_per_hour=0,
                    vertical_main_green=0,
                    horizontal_main_green=0,
                    vertical_right_green=0,
                    horizontal_right_green=0
                )
            db.session.add(tl_config)
            db.session.commit()
            print(f"✅ Traffic settings stored for run_id {config.run_id}")

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

            try:
                
                response = requests.post("http://127.0.0.1:8000/update_spawn_rates", json=spawn_rates)
                
                if response.status_code == 200:
                    print("✅ Spawn rates sent successfully to server.py.")
            
            except requests.exceptions.RequestException as e:
             
                print(f"⚠️ Could not reach server.py: {e}")

            junction_settings = {
                "lanes": int(data.get('lanes', 5)),
                "left_turn_lane": 'left-turn' in data,
                "bus_lane": 'bus_lane' in data,
                "pedestrian_duration": safe_int(data.get('pedestrian-duration', 0)),
                "pedestrian_frequency":  safe_int(data.get('pedestrian-frequency', 0)),
            }

            try:
                
                response = requests.post("http://127.0.0.1:8000/update_junction_settings", json=junction_settings)
                
                if response.status_code == 200:
                    print("✅ Junction settings sent successfully to server.py.")
                
                else:
                    print(f"❌ Error sending junction settings: {response.text}")
            
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not reach server.py: {e}")


            traffic_light_settings = {
                    "traffic-light-enable": "on" if traffic_enabled else "",  # or just traffic_enabled
                    "sequences": tl_config.sequences_per_hour,
                    "vertical_main_green": tl_config.vertical_main_green,
                    "horizontal_main_green": tl_config.horizontal_main_green,
                    "vertical_right_green": tl_config.vertical_right_green,
                    "horizontal_right_green": tl_config.horizontal_right_green
            }

            try:
                response = requests.post("http://127.0.0.1:8000/update_traffic_light_settings", json=traffic_light_settings)
                if response.status_code == 200:
                    print("Traffic light settings sent successfully to server.py.")
                else:
                    print(f"Error sending traffic light settings: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not reach server.py for traffic lights: {e}")

            return redirect(url_for('junctionPage')) 

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return jsonify({'error': str(e)}), 400

    return render_template('parameters.html')


@app.route("/junction_settings_proxy", methods=["GET"])
def junction_settings_proxy():
    """
    
    """
    
    try:
        resp = requests.get("http://127.0.0.1:8000/junction_settings")
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-file', methods=['POST'])
def uploadfile():
    """
    
    """
    
    if 'file' not in request.files:
        return "No file part in the request.", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No file selected.", 400

    return f"File '{file.filename}' uploaded successfully!"

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    
    """
    
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


def simulate():
    """
    
    """
    
    try:
    
        data = request.json
        run_id = data.get('run_id')
        session_id = data.get('session_id')
        
        sim_response = requests.get("http://localhost:8000/simulate_fast") 
        sim_response.raise_for_status()  
        
        metrics = sim_response.json()

        user_metrics = metrics["user"]
        algorithm_metrics = metrics["default"]
        algorithm_traffic_settings = metrics["default_traffic_settings"]

        default_traffic_result = AlgorithmTrafficSettings(
            run_id=run_id,
            session_id=session_id,
            enabled=algorithm_traffic_settings.get("enabled", False),
            sequences_per_hour=algorithm_traffic_settings.get("sequences_per_hour", 0),
            vertical_main_green=algorithm_traffic_settings.get("vertical_main_green", 0),
            horizontal_main_green=algorithm_traffic_settings.get("horizontal_main_green", 0),
            vertical_right_green=algorithm_traffic_settings.get("vertical_right_green", 0),
            horizontal_right_green=algorithm_traffic_settings.get("horizontal_right_green", 0)
        )
        
        db.session.add(default_traffic_result)
        db.session.commit()

        save_session_leaderboard_result(
            run_id, session_id,
            user_metrics["avg_wait_time_n"], user_metrics["max_wait_time_n"], user_metrics["max_queue_length_n"],
            user_metrics["avg_wait_time_s"], user_metrics["max_wait_time_s"], user_metrics["max_queue_length_s"],
            user_metrics["avg_wait_time_e"], user_metrics["max_wait_time_e"], user_metrics["max_queue_length_e"],
            user_metrics["avg_wait_time_w"], user_metrics["max_wait_time_w"], user_metrics["max_queue_length_w"]
        )
        
        save_algorithm_result(
            run_id, session_id,
            algorithm_metrics["avg_wait_time_n"], algorithm_metrics["max_wait_time_n"], algorithm_metrics["max_queue_length_n"],
            algorithm_metrics["avg_wait_time_s"], algorithm_metrics["max_wait_time_s"], algorithm_metrics["max_queue_length_s"],
            algorithm_metrics["avg_wait_time_e"], algorithm_metrics["max_wait_time_e"], algorithm_metrics["max_queue_length_e"],
            algorithm_metrics["avg_wait_time_w"], algorithm_metrics["max_wait_time_w"], algorithm_metrics["max_queue_length_w"]
        )
        
        user_score = compute_score_4directions(
            user_metrics["avg_wait_time_n"], user_metrics["max_wait_time_n"], user_metrics["max_queue_length_n"],
            user_metrics["avg_wait_time_s"], user_metrics["max_wait_time_s"], user_metrics["max_queue_length_s"],
            user_metrics["avg_wait_time_e"], user_metrics["max_wait_time_e"], user_metrics["max_queue_length_e"],
            user_metrics["avg_wait_time_w"], user_metrics["max_wait_time_w"], user_metrics["max_queue_length_w"], 
            False
        )
        
        default_score = compute_score_4directions(
            algorithm_metrics["avg_wait_time_n"], algorithm_metrics["max_wait_time_n"], algorithm_metrics["max_queue_length_n"],
            algorithm_metrics["avg_wait_time_s"], algorithm_metrics["max_wait_time_s"], algorithm_metrics["max_queue_length_s"],
            algorithm_metrics["avg_wait_time_e"], algorithm_metrics["max_wait_time_e"], algorithm_metrics["max_queue_length_e"],
            algorithm_metrics["avg_wait_time_w"], algorithm_metrics["max_wait_time_w"], algorithm_metrics["max_queue_length_w"],
            True
        )
        
        return jsonify({
            "message": "sim results saved",
            "user": {
                "max_wait_time_n": user_metrics["max_wait_time_n"],
                "max_wait_time_s": user_metrics["max_wait_time_s"],
                "max_wait_time_e": user_metrics["max_wait_time_e"],
                "max_wait_time_w": user_metrics["max_wait_time_w"],
                "max_queue_length_n": user_metrics["max_queue_length_n"],
                "max_queue_length_s": user_metrics["max_queue_length_s"],
                "max_queue_length_e": user_metrics["max_queue_length_e"],
                "max_queue_length_w": user_metrics["max_queue_length_w"],
                "avg_wait_time_n": user_metrics["avg_wait_time_n"],
                "avg_wait_time_s": user_metrics["avg_wait_time_s"],
                "avg_wait_time_e": user_metrics["avg_wait_time_e"],
                "avg_wait_time_w": user_metrics["avg_wait_time_w"],
                "score": user_score
            },
            "default": {
                "max_wait_time_n": algorithm_metrics["max_wait_time_n"],
                "max_wait_time_s": algorithm_metrics["max_wait_time_s"],
                "max_wait_time_e": algorithm_metrics["max_wait_time_e"],
                "max_wait_time_w": algorithm_metrics["max_wait_time_w"],
                "max_queue_length_n": algorithm_metrics["max_queue_length_n"],
                "max_queue_length_s": algorithm_metrics["max_queue_length_s"],
                "max_queue_length_e": algorithm_metrics["max_queue_length_e"],
                "max_queue_length_w": algorithm_metrics["max_queue_length_w"],
                "avg_wait_time_n": algorithm_metrics["avg_wait_time_n"],
                "avg_wait_time_s": algorithm_metrics["avg_wait_time_s"],
                "avg_wait_time_e": algorithm_metrics["avg_wait_time_e"],
                "avg_wait_time_w": algorithm_metrics["avg_wait_time_w"],
                "score": default_score
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/junctionPage')
def junctionPage():
    """
    
    """
    
    return render_template('junctionPage.html')

@app.route('/leaderboards')
def leaderboards():
    """
    
    """
    
    results = get_all_time_best_configurations()
    
    return render_template('leaderboards.html', results=results)


def get_all_time_best_configurations():
    """
    
    """
    
    all_results = LeaderboardResult.query.all()
    results_with_scores = []
    
    for r in all_results:

        score = compute_score_4directions(

            r.avg_wait_time_north, r.max_wait_time_north, r.max_queue_length_north,

            r.avg_wait_time_south, r.max_wait_time_south, r.max_queue_length_south,

            r.avg_wait_time_east, r.max_wait_time_east, r.max_queue_length_east,

            r.avg_wait_time_west, r.max_wait_time_west, r.max_queue_length_west,

            False
        )

        r.score = score

        results_with_scores.append(r)
    
    results_with_scores.sort(key=lambda x: x.score)
    
    return results_with_scores[:10]

@app.route('/session_leaderboard')
def session_leaderboard_page():
    """
    
    """
    
    session_id = request.args.get('session_id', type=int)
    
    if not session_id:
        active_session = Session.query.filter_by(active=True).order_by(Session.id.desc()).first()
        session_id = active_session.id if active_session else None
    
    runs = get_recent_runs_with_scores(session_id) if session_id else []
    
    return render_template('session_leaderboard.html', runs=runs)

@app.route('/simulate', methods=['POST'])
def simulate_endpoint():
    return simulate()  # Your existing simulate() function


def get_global_extremes(for_algorithm_bool):
    """
    
    """
    
    if for_algorithm_bool:
        results = AlgorithmLeaderboardResult.query.all()
    else:
        results = LeaderboardResult.query.all()
    
    if not results:

        return {
            "north": {"best_avg": None, "worst_avg": None, "best_max": None, "worst_max": None, "best_queue": None, "worst_queue": None},
            "south": {"best_avg": None, "worst_avg": None, "best_max": None, "worst_max": None, "best_queue": None, "worst_queue": None},
            "east": {"best_avg": None, "worst_avg": None, "best_max": None, "worst_max": None, "best_queue": None, "worst_queue": None},
            "west": {"best_avg": None, "worst_avg": None, "best_max": None, "worst_max": None, "best_queue": None, "worst_queue": None},
        }

    north_avg_values = [r.avg_wait_time_north for r in results]
    north_max_values = [r.max_wait_time_north for r in results]
    north_queue_values = [r.max_queue_length_north for r in results]

    south_avg_values = [r.avg_wait_time_south for r in results]
    south_max_values = [r.max_wait_time_south for r in results]
    south_queue_values = [r.max_queue_length_south for r in results]

    east_avg_values = [r.avg_wait_time_east for r in results]
    east_max_values = [r.max_wait_time_east for r in results]
    east_queue_values = [r.max_queue_length_east for r in results]

    west_avg_values = [r.avg_wait_time_west for r in results]
    west_max_values = [r.max_wait_time_west for r in results]
    west_queue_values = [r.max_queue_length_west for r in results]

    return {
        "north": {
            "best_avg": min(north_avg_values),
            "worst_avg": max(north_avg_values),
            "best_max": min(north_max_values),
            "worst_max": max(north_max_values),
            "best_queue": min(north_queue_values),
            "worst_queue": max(north_queue_values),
        },
        "south": {
            "best_avg": min(south_avg_values),
            "worst_avg": max(south_avg_values),
            "best_max": min(south_max_values),
            "worst_max": max(south_max_values),
            "best_queue": min(south_queue_values),
            "worst_queue": max(south_queue_values),
        },
        "east": {
            "best_avg": min(east_avg_values),
            "worst_avg": max(east_avg_values),
            "best_max": min(east_max_values),
            "worst_max": max(east_max_values),
            "best_queue": min(east_queue_values),
            "worst_queue": max(east_queue_values),
        },
        "west": {
            "best_avg": min(west_avg_values),
            "worst_avg": max(west_avg_values),
            "best_max": min(west_max_values),
            "worst_max": max(west_max_values),
            "best_queue": min(west_queue_values),
            "worst_queue": max(west_queue_values),
        }
    }

def compute_score_4directions(
    nb_avg, nb_max, nb_queue,
    sb_avg, sb_max, sb_queue,
    eb_avg, eb_max, eb_queue,
    wb_avg, wb_max, wb_queue,
    for_algorithm_bool
):
    """
    
    """
    
    extremes = get_global_extremes(for_algorithm_bool)
    
    nb_best_avg = extremes["north"]["best_avg"]
    nb_worst_avg = extremes["north"]["worst_avg"]
    nb_best_max = extremes["north"]["best_max"]
    nb_worst_max = extremes["north"]["worst_max"]
    nb_best_queue = extremes["north"]["best_queue"]
    nb_worst_queue = extremes["north"]["worst_queue"]

    sb_best_avg = extremes["south"]["best_avg"]
    sb_worst_avg = extremes["south"]["worst_avg"]
    sb_best_max = extremes["south"]["best_max"]
    sb_worst_max = extremes["south"]["worst_max"]
    sb_best_queue = extremes["south"]["best_queue"]
    sb_worst_queue = extremes["south"]["worst_queue"]

    eb_best_avg = extremes["east"]["best_avg"]
    eb_worst_avg = extremes["east"]["worst_avg"]
    eb_best_max = extremes["east"]["best_max"]
    eb_worst_max = extremes["east"]["worst_max"]
    eb_best_queue = extremes["east"]["best_queue"]
    eb_worst_queue = extremes["east"]["worst_queue"]

    wb_best_avg = extremes["west"]["best_avg"]
    wb_worst_avg = extremes["west"]["worst_avg"]
    wb_best_max = extremes["west"]["best_max"]
    wb_worst_max = extremes["west"]["worst_max"]
    wb_best_queue = extremes["west"]["best_queue"]
    wb_worst_queue = extremes["west"]["worst_queue"]

    def normalize(x, best, worst):
        """
    
        """
    
        if best == worst:
            
            return 0
        
        return 100.0 * (x - best) / (worst - best)

    s_nb_avg = normalize(nb_avg, nb_best_avg, nb_worst_avg)
    s_nb_max = normalize(nb_max, nb_best_max, nb_worst_max)
    s_nb_queue = normalize(nb_queue, nb_best_queue, nb_worst_queue)
    nb_direction_score = (s_nb_avg + s_nb_max + s_nb_queue) / 3.0

    s_sb_avg = normalize(sb_avg, sb_best_avg, sb_worst_avg)
    s_sb_max = normalize(sb_max, sb_best_max, sb_worst_max)
    s_sb_queue = normalize(sb_queue, sb_best_queue, sb_worst_queue)
    sb_direction_score = (s_sb_avg + s_sb_max + s_sb_queue) / 3.0

    s_eb_avg = normalize(eb_avg, eb_best_avg, eb_worst_avg)
    s_eb_max = normalize(eb_max, eb_best_max, eb_worst_max)
    s_eb_queue = normalize(eb_queue, eb_best_queue, eb_worst_queue)
    eb_direction_score = (s_eb_avg + s_eb_max + s_eb_queue) / 3.0

    s_wb_avg = normalize(wb_avg, wb_best_avg, wb_worst_avg)
    s_wb_max = normalize(wb_max, wb_best_max, wb_worst_max)
    s_wb_queue = normalize(wb_queue, wb_best_queue, wb_worst_queue)
    wb_direction_score = (s_wb_avg + s_wb_max + s_wb_queue) / 3.0

    final_score = nb_direction_score + sb_direction_score + eb_direction_score + wb_direction_score

    return final_score

def get_recent_runs_with_scores(session_id):
    """
    
    """
    
    recent_runs = (
        LeaderboardResult.query
        .filter_by(session_id=session_id)
        .order_by(LeaderboardResult.run_id.desc())
        .limit(10)
        .all()
    )
    
    runs_with_scores = []

    for r in recent_runs:
        final_score = compute_score_4directions(
            # 12 actual metrics
            r.avg_wait_time_north, r.max_wait_time_north, r.max_queue_length_north,
            r.avg_wait_time_south, r.max_wait_time_south, r.max_queue_length_south,
            r.avg_wait_time_east,  r.max_wait_time_east,  r.max_queue_length_east,
            r.avg_wait_time_west,  r.max_wait_time_west,  r.max_queue_length_west,
            False
        )

        runs_with_scores.append({
            "run_id": r.run_id,

            "nb_avg_wait": r.avg_wait_time_north,
            "nb_max_wait": r.max_wait_time_north,
            "nb_max_queue": r.max_queue_length_north,

            "sb_avg_wait": r.avg_wait_time_south,
            "sb_max_wait": r.max_wait_time_south,
            "sb_max_queue": r.max_queue_length_south,

            "eb_avg_wait": r.avg_wait_time_east,
            "eb_max_wait": r.max_wait_time_east,
            "eb_max_queue": r.max_queue_length_east,

            "wb_avg_wait": r.avg_wait_time_west,
            "wb_max_wait": r.max_wait_time_west,
            "wb_max_queue": r.max_queue_length_west,

            "score": final_score
        })

    if not runs_with_scores:
        return []

    best_run = min(runs_with_scores, key=lambda x: x["score"])

    runs_with_scores.remove(best_run)

    runs_with_scores.sort(key=lambda x: x["run_id"], reverse=True)
    
    final_list = [best_run] + runs_with_scores

    return final_list

@app.route('/junction_details')
def junction_details():
    run_id = request.args.get('run_id', type=int)

    # If no run_id is provided, get the latest run_id
    if not run_id:
        latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()
        if latest_config:
            run_id = latest_config.run_id
        else:
            flash('No run ID provided and no configurations exist.')
            return redirect('/session_leaderboard')

    # Retrieve configuration based on run_id
    configuration = Configuration.query.filter_by(run_id=run_id).first()
    if not configuration:
        flash('Configuration details not found for the provided run.')
        return redirect('/session_leaderboard')

    # Retrieve traffic light settings for the run_id
    traffic_light_settings = TrafficSettings.query.filter_by(run_id=run_id).first()

    # If no traffic settings exist, provide default values
    if not traffic_light_settings:
        traffic_light_settings = {
            "enabled": False,
            "sequences_per_hour": 0,
            "vertical_main_green": 0,
            "horizontal_main_green": 0,
            "vertical_right_green": 0,
            "horizontal_right_green": 0
        }
    else:
        # Convert SQLAlchemy object to dictionary (if found)
        traffic_light_settings = {
            "enabled": traffic_light_settings.enabled,
            "sequences_per_hour": traffic_light_settings.sequences_per_hour,
            "vertical_main_green": traffic_light_settings.vertical_main_green,
            "horizontal_main_green": traffic_light_settings.horizontal_main_green,
            "vertical_right_green": traffic_light_settings.vertical_right_green,
            "horizontal_right_green": traffic_light_settings.horizontal_right_green
        }

    return render_template(
        'junction_details.html',
        configuration=configuration,
        traffic_light_settings=traffic_light_settings
    )


if __name__ == '__main__':
    app.run(debug=True)