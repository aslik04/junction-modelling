"""
Traffic Junction Simulator Flask Application

This module implements a Flask web application that manages a traffic junction simulation.
It provides endpoints for starting/stopping a FastAPI-based simulation server, submitting
and uploading configuration parameters (via forms or JSON), and retrieving simulation 
results and leaderboard metrics.

Key features include:
  - Integration with a FastAPI backend to simulate traffic scenarios.
  - Database management with SQLAlchmy for storing simulation configurations, session data,
    and performance metrics.
  - Multiple endpoints for handling file uploads, parameter submissions, simulation control,
    and retrieval of simulation results and leaderbords.
  - Calculation of custom scores based on wait times and queue lengths for different directions.

Usage:
    python app.py

Author: Group_33
"""

import os
import sys
import time
import subprocess
import csv
import io
from io import StringIO
import requests
from flask import Flask, flash, request, jsonify, render_template, url_for, redirect, send_from_directory, Response
from models import db, Configuration, LeaderboardResult, Session, TrafficSettings, AlgorithmLeaderboardResult
from sqlalchemy import inspect, and_
import json

app = Flask(__name__)

app.secret_key = "Group_33" 

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'traffic_junction.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

global_session_id = 0

with app.app_context():
    """
    Initialise database and create all tables.
    """
    
    db.create_all()

server_process = None

def start_fastapi():
    """
    Start the FastAPI server as a subprocess.
    
    It provides a small delay to allow the server to intialise.
    
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
    If the proces does not terminate within the timeout,
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
        tuple: A JSON response with a succes message and 200 status code.
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
    Create a new databse session for tracking simulations.
    
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
        session_id (int): The ID of the sesion to be ended.
    """
    
    session = Session.query.get(session_id)
    
    if session:
        session.active = False
        db.session.commit()

def get_session_leaderboard(session):
    """
    Get the top 10 leaderboard results for a session based on computed scores.

    Retrieves all leaderboard results for a given session, computes a score for each
    using compute_score_4directons, sorts them, and returns the top 10.

    Args:
        session (int): The session ID to filter results.

    Returns:
        list: The top 10 leaderboard results sorted by their calculated score.
    """
    results = LeaderboardResult.query.filter_by(session_id=session).all()
    
    if not results:
        return []

    for result in results:

        result.calculated_score = compute_score_4directions(
            result.run_id,
            result.session_id,
            result.avg_wait_time_north, result.max_wait_time_north, result.max_queue_length_north,
            result.avg_wait_time_south, result.max_wait_time_south, result.max_queue_length_south,
            result.avg_wait_time_east, result.max_wait_time_east, result.max_queue_length_east,
            result.avg_wait_time_west, result.max_wait_time_west, result.max_queue_length_west,
        )

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
        run_id (int): Unique for the simulatoin run.
        session_id (int): ID of the session
        avg_wait_time_n (float): Average wait time for north-bound traffic.
        max_wait_time_n (float): Maxium wait time for north-bound traffic.
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
    Save algorithm's simulation metrics to the leaderboard.

    Stores the performace metrics from the algorithm's simulation run.

    Args:
        run_id (int): Identifies simulation run
        session_id (int): Identifies session
        avg_wait_time_n (float): Average wait time for northbound.
        max_wait_time_n (float): Maximum wait time for notrhbound.
        max_queue_length_n (int): Maximum queue length for northbound.
        # Similar parameters for south, east, and west directions

    Returns:
        None.
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
    Retrieve the latest rates for taffic from the most recent inputs.
    
    Returns:
        dict: A nested dictionary containing rates for each direction 
              and movmeent type (forward, left, right).
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
              like nuber of lanes, pedestrian settings, etc.
    """
    try:

        latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()

        if latest_config:
           
            return {
                "lanes": latest_config.lanes,
                "left_turn_lane": latest_config.left_turn_lane,
                "pedestrian_duration": latest_config.pedestrian_duration,
                "pedestrian_frequency": latest_config.pedestrian_frequency
            }
        else:

            return {
                "lanes": 5,
                "pedestrian_duration": 0,
                "pedestrian_frequency": 0
            }
    except Exception as e:
        
        print("Error retrieving configuration:", e)
        
        return {
            "lanes": 5,
            "pedestrian_duration": 0,
            "pedestrian_frequency": 0
        }

def process_csv(file):
    """
    Read a CSV file from the upload and convert each row into a Configuration object
    which will be aded to the database in the future.

    Args:
        file: The uploaded file object.

    Returns:
        list: A list of Configuration objects created from the CSV rows.
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
    Start a new session and return its ID.

    Returns:
        JSON: A message and the new session ID.
    """
    
    session_id = create_session()
    
    return jsonify({"session_id": session_id, "message": "Session started"})

@app.route('/end_session', methods=['POST'])
def end_session_api():
    """
    End the current session.

    Returns:
        JSON: A confirmation message that the session has ended.
    """
    
    session_id = request.json.get('session_id')
    
    end_session(session_id)
    
    return jsonify({'message': 'Session ended'})

@app.route('/')
def index():
    """
    Create a new session and render the index page with the sesion ID.

    Returns:
        Renders index page.
    """

    global global_session_id
    
    global_session_id = create_session()
    
    return render_template('index.html', session_id=global_session_id)

@app.route('/index')
def indexTwo():
    """
    Starts a session and rendrs the index page.

    Returns:
        Renders index page.
    """

    global global_session_id

    global_session_id = create_session()
    
    return render_template('index.html', session_id=global_session_id)

@app.route('/get_session_run_id', methods=['GET'])
def get_session_run_id():
    """
    Retrieve the latest active session and its run ID.

    Creates a new session if any doest exist, and defaults the run ID to 1 if necessary.

    Returns:
        JSON: The session ID and run ID.
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
        
        print(f"Error retrieving session and run_id: {e}")
        
        return jsonify({"error": str(e)}), 500


@app.route('/results')
def results():
    """
    Simulate a traffic run and render the results page with computed metrics.

    Processes simulation metrics, gets the current settings, and renders the results page.

    Returns:
        Renders results page or an error JSON.
    """
    
    try:
        session_id = request.args.get('session_id', type=int)

        if not session_id:
            if global_session_id == 0:
                return jsonify({"error": "Missing session_id"}), 400   
            else:             
                session_id = global_session_id

        print(session_id)

        run_id = request.args.get('run_id', type=int)

        if not run_id:
            return jsonify({"error": "Missing run_id"}), 400

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

        return render_template(
            'results.html',
            session_id=session_id,
            run_id=run_id,
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
            algorithm_metrics=algorithm_metrics
        )

    except Exception as e:        
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 400
    
@app.route('/back_to_results')
def back_to_results():
    """
    Retrieve the latset configuration and settings to render the results page again.

    Returns:
        Rendered results template with current configuration, spawn rates, and calculated scores.
    """
    
    try:

        latest_config = Configuration.query.order_by(Configuration.run_id.desc()).first()
        if latest_config:
            run_id = latest_config.run_id
            session_id = latest_config.session_id
        else:
            return jsonify({"error": "Missing run_id"}), 400

        configuration = Configuration.query.filter_by(session_id=session_id).first()

        if not configuration:
            flash('Configuration details not found for the provided run.')
            return redirect(url_for('error', message=f"Configuration for Run: {str(run_id)} in Session: {str(session_id)} does not exist."))
        
        junction_settings = {
            "lanes": configuration.lanes,
            "left_turn_lane": configuration.left_turn_lane,
            "pedestrian_duration": configuration.pedestrian_duration,
            "pedestrian_frequency": configuration.pedestrian_frequency
        }

        spawn_rates = {
            "north": {
                "forward": configuration.north_forward_vph,
                "left": configuration.north_left_vph,
                "right": configuration.north_right_vph
            },
            "south": {
                "forward": configuration.south_forward_vph,
                "left": configuration.south_left_vph,
                "right": configuration.south_right_vph
            },
            "east": {
                "forward": configuration.east_forward_vph,
                "left": configuration.east_left_vph,
                "right": configuration.east_right_vph
            },
            "west": {
                "forward": configuration.west_forward_vph,
                "left": configuration.west_left_vph,
                "right": configuration.west_right_vph
            }
        }

        traffic_light_settings = {
            "enabled": False,
            "sequences_per_hour": 0,
            "vertical_main_green": 0,
            "horizontal_main_green": 0,
            "vertical_right_green": 0,
            "horizontal_right_green": 0
        }
        avg_wait_time_n = avg_wait_time_s = avg_wait_time_e = avg_wait_time_w = 0
        max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0
        max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0
        score = 0.0

        tls_obj = (
            TrafficSettings.query
            .filter_by(run_id=run_id)
            .order_by(TrafficSettings.id.desc())
            .first()
        )

        if not tls_obj:
            traffic_light_settings = {
                "enabled": False,
                "sequences_per_hour": 0,
                "vertical_main_green": 0,
                "horizontal_main_green": 0,
                "vertical_right_green": 0,
                "horizontal_right_green": 0
            }
        else:
            traffic_light_settings = {
                "enabled": tls_obj.enabled,
                "sequences_per_hour": tls_obj.sequences_per_hour,
                "vertical_main_green": tls_obj.vertical_main_green,
                "horizontal_main_green": tls_obj.horizontal_main_green,
                "vertical_right_green": tls_obj.vertical_right_green,
                "horizontal_right_green": tls_obj.horizontal_right_green
            }

        user_result = LeaderboardResult.query.filter_by(run_id=run_id, session_id=session_id).first()
        if user_result:
            avg_wait_time_n=user_result.avg_wait_time_north
            avg_wait_time_s=user_result.avg_wait_time_south
            avg_wait_time_e=user_result.avg_wait_time_east
            avg_wait_time_w=user_result.avg_wait_time_west
            max_wait_time_n=user_result.max_wait_time_north
            max_wait_time_s=user_result.max_wait_time_south
            max_wait_time_e=user_result.max_wait_time_east
            max_wait_time_w=user_result.max_wait_time_west
            max_queue_length_n=user_result.max_queue_length_north
            max_queue_length_s=user_result.max_queue_length_south
            max_queue_length_e=user_result.max_queue_length_east
            max_queue_length_w=user_result.max_queue_length_west

            score = compute_score_4directions(
                run_id,
                session_id,
                user_result.avg_wait_time_north,
                user_result.max_wait_time_north,
                user_result.max_queue_length_north,
                user_result.avg_wait_time_south,
                user_result.max_wait_time_south,
                user_result.max_queue_length_south,
                user_result.avg_wait_time_east,
                user_result.max_wait_time_east,
                user_result.max_queue_length_east,
                user_result.avg_wait_time_west,
                user_result.max_wait_time_west,
                user_result.max_queue_length_west
            )
        else:
            avg_wait_time_n = 0
            avg_wait_time_s = 0
            avg_wait_time_e = 0
            avg_wait_time_w = 0
            max_wait_time_n = 0
            max_wait_time_s = 0
            max_wait_time_e = 0
            max_wait_time_w = 0
            max_queue_length_n = 0
            max_queue_length_s = 0
            max_queue_length_e = 0
            max_queue_length_w = 0
            score = 0.0

        # Query algorithm leaderboard result.
        algo_result = AlgorithmLeaderboardResult.query.filter_by(run_id=run_id, session_id=session_id).first()
        if algo_result:
            algorithm_metrics = {
                "avg_wait_time_n": algo_result.avg_wait_time_north,
                "avg_wait_time_s": algo_result.avg_wait_time_south,
                "avg_wait_time_e": algo_result.avg_wait_time_east,
                "avg_wait_time_w": algo_result.avg_wait_time_west,
                "max_wait_time_n": algo_result.max_wait_time_north,
                "max_wait_time_s": algo_result.max_wait_time_south,
                "max_wait_time_e": algo_result.max_wait_time_east,
                "max_wait_time_w": algo_result.max_wait_time_west,
                "max_queue_length_n": algo_result.max_queue_length_north,
                "max_queue_length_s": algo_result.max_queue_length_south,
                "max_queue_length_e": algo_result.max_queue_length_east,
                "max_queue_length_w": algo_result.max_queue_length_west,
            }
            algorithm_metrics["score"] = compute_score_4directions(
                run_id,
                session_id,
                algorithm_metrics["avg_wait_time_n"],
                algorithm_metrics["max_wait_time_n"],
                algorithm_metrics["max_queue_length_n"],
                algorithm_metrics["avg_wait_time_s"],
                algorithm_metrics["max_wait_time_s"],
                algorithm_metrics["max_queue_length_s"],
                algorithm_metrics["avg_wait_time_e"],
                algorithm_metrics["max_wait_time_e"],
                algorithm_metrics["max_queue_length_e"],
                algorithm_metrics["avg_wait_time_w"],
                algorithm_metrics["max_wait_time_w"],
                algorithm_metrics["max_queue_length_w"]
            )
        else:
            algorithm_metrics = {
                "avg_wait_time_n": 0, "avg_wait_time_s": 0, "avg_wait_time_e": 0, "avg_wait_time_w": 0,
                "max_wait_time_n": 0, "max_wait_time_s": 0, "max_wait_time_e": 0, "max_wait_time_w": 0,
                "max_queue_length_n": 0, "max_queue_length_s": 0, "max_queue_length_e": 0, "max_queue_length_w": 0,
                "score": 0.0
            }        

        return render_template(
            'results.html',
            session_id=session_id,
            run_id=run_id,
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
            algorithm_metrics=algorithm_metrics
        )

    except Exception as e:        
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 400    

def get_latest_traffic_light_settings():
    """
    Get the most recent traffic light settings or default valeus if none exist.

    Returns:
        dict: A dictionary with the latest traffic light configuration.
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
    Fetch the leaderboard result for a given session and run.

    Args:
        session_id (int): To identify the session.
        run_id (int): To identify the run.

    Returns:
        LeaderboardResult: The leaderboard result object.
    """
    
    return LeaderboardResult.query.filter_by(session_id=session_id, run_id=run_id).first()

@app.route('/parameters', methods=['GET', 'POST'])
def parameters():
    """
    Handles manual parameter submission.
    On POST, it extracts form data, stores configuration in the database,
    and sends spawn rates, junction settings, and trafic light settings
    to the fastapi server. On GET, it renders the parameters page.
    """
    if request.method == 'POST':
        print("Received Form Data:", request.form)
        try:
            data = request.form
            print("Received Form Data:", data)

            required_fields = [
                'nb_forward', 'nb_left', 'nb_right',
                'sb_forward', 'sb_left', 'sb_right',
                'eb_forward', 'eb_left', 'eb_right',
                'wb_forward', 'wb_left', 'wb_right'
            ]

            for field in required_fields:
                if field not in data or not data[field].strip():

                    return redirect(url_for('error', message=f"Missing required field: {field}"))

            session = Session.query.get(global_session_id)

            print(global_session_id)

            def safe_int(value):
                try:
                    val = str(value).strip()
                    return int(val) if val.isdigit() else 0
                except Exception:
                    return 0

            north_vph = safe_int(data.get('nb_forward', 0)) + safe_int(data.get('nb_left', 0)) + safe_int(data.get('nb_right', 0))
            south_vph = safe_int(data.get('sb_forward', 0)) + safe_int(data.get('sb_left', 0)) + safe_int(data.get('sb_right', 0))
            east_vph  = safe_int(data.get('eb_forward', 0)) + safe_int(data.get('eb_left', 0)) + safe_int(data.get('eb_right', 0))
            west_vph  = safe_int(data.get('wb_forward', 0)) + safe_int(data.get('wb_left', 0)) + safe_int(data.get('wb_right', 0))

            pedestrian_duration = safe_int(data.get('pedestrian-duration', 0))
            pedestrian_frequency = safe_int(data.get('pedestrian-frequency', 0))

            # Create and store the configuration
            config = Configuration(
                session_id=session.id,
                lanes=safe_int(data.get('lanes', 5)),
                pedestrian_duration=pedestrian_duration,
                pedestrian_frequency=pedestrian_frequency,

                north_vph=north_vph,
                north_forward_vph=safe_int(data.get('nb_forward', 0)),
                north_left_vph=safe_int(data.get('nb_left', 0)),
                north_right_vph=safe_int(data.get('nb_right', 0)),

                south_vph=south_vph,
                south_forward_vph=safe_int(data.get('sb_forward', 0)),
                south_left_vph=safe_int(data.get('sb_left', 0)),
                south_right_vph=safe_int(data.get('sb_right', 0)),

                east_vph=east_vph,
                east_forward_vph=safe_int(data.get('eb_forward', 0)),
                east_left_vph=safe_int(data.get('eb_left', 0)),
                east_right_vph=safe_int(data.get('eb_right', 0)),

                west_vph=west_vph,
                west_forward_vph=safe_int(data.get('wb_forward', 0)),
                west_left_vph=safe_int(data.get('wb_left', 0)),
                west_right_vph=safe_int(data.get('wb_right', 0))
            )
            db.session.add(config)
            db.session.commit()
            print(f"Data stored with run_id {config.run_id}")

            traffic_enabled = data.get('traffic-light-enable', '') == 'on'
            if traffic_enabled:
                tl_config = TrafficSettings(
                    run_id=config.run_id,
                    session_id=session.id,
                    enabled=True,
                    sequences_per_hour=safe_int(data.get('tl_sequences', 0)),
                    vertical_main_green=safe_int(data.get('tl_vmain', 0)),
                    horizontal_main_green=safe_int(data.get('tl_hmain', 0)),
                    vertical_right_green=safe_int(data.get('tl_vright', 0)),
                    horizontal_right_green=safe_int(data.get('tl_hright', 0))
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
            print(f"Traffic settings stored for run_id {config.run_id}")

            # Build spawn rates dictionary to send to FastAPI
            spawn_rates = {
                "north": {
                    "forward": safe_int(data.get('nb_forward', 0)),
                    "left": safe_int(data.get('nb_left', 0)),
                    "right": safe_int(data.get('nb_right', 0))
                },
                "south": {
                    "forward": safe_int(data.get('sb_forward', 0)),
                    "left": safe_int(data.get('sb_left', 0)),
                    "right": safe_int(data.get('sb_right', 0))
                },
                "east": {
                    "forward": safe_int(data.get('eb_forward', 0)),
                    "left": safe_int(data.get('eb_left', 0)),
                    "right": safe_int(data.get('eb_right', 0))
                },
                "west": {
                    "forward": safe_int(data.get('wb_forward', 0)),
                    "left": safe_int(data.get('wb_left', 0)),
                    "right": safe_int(data.get('wb_right', 0))
                }
            }
            try:
                response = requests.post("http://127.0.0.1:8000/update_spawn_rates", json=spawn_rates)
                if response.status_code == 200:
                    print("Spawn rates sent successfully to server.py.")
            except requests.exceptions.RequestException as e:
                print(f"Could not reach server.py: {e}")

            junction_settings = {
                "lanes": safe_int(data.get('lanes', 5)),
                "pedestrian_duration": pedestrian_duration,
                "pedestrian_frequency": pedestrian_frequency,
            }
            try:
                response = requests.post("http://127.0.0.1:8000/update_junction_settings", json=junction_settings)
                if response.status_code == 200:
                    print("Junction settings sent successfully to server.py.")
                else:
                    print(f"Error sending junction settings: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Could not reach server.py: {e}")

            traffic_light_settings = {
                "traffic-light-enable": "on" if traffic_enabled else "",
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
                print(f"Could not reach server.py for traffic lights: {e}")

            return redirect(url_for('junctionPage'))
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            return jsonify({'error': str(e)}), 400

    return render_template('parameters.html')


@app.route("/junction_settings_proxy", methods=["GET"])
def junction_settings_proxy():
    """
    Retrieve junction settings from the FastAPI service.

    Sends a GET request to the fastAPI endpoint
    In an error, returns a eror message with a 500 status code.

    Returns:
        Response: A response containing the juncion settings or an error message.
    """
    
    try:
        resp = requests.get("http://127.0.0.1:8000/junction_settings")
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-file', methods=['POST'])
def uploadfile():
    """
    Handle file upload, ensures that a file is actually recieved
    Returns:
        str: A success or error message.
    """
    
    if 'file' not in request.files:
        return "No file part in the request.", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No file selected.", 400

    return f"File '{file.filename}' uploaded successfully!"

@app.route('/upload', methods=['POST'])
def upload():
    """
    Process file upload and updte configuration and traffic settings.

    Handles a file upload making sure that a file is provided and that its extension is '.json'
    Parses the file to extract input parmaeters. Stores the configuration
    and traffic settings in the database, and sends data to other endpoints. 

    Returns:
        Response: A response containing a redirect URL to the junction page and lane information,
                  or an error message with a 400 status code.
    """

    stop_fastapi()
    start_fastapi()

    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.json', '.csv']:
        return render_template('failure.html')

    # Build a dictionary that will mimic the form data from /parameters
    data = {}
    try:
        if ext == '.json':
            file_content = file.read().decode('utf-8')
            json_data = json.loads(file_content)
            
            vehicle = json_data.get("vehicle_settings", {})
            north = vehicle.get("north", {})
            east = vehicle.get("east", {})
            south = vehicle.get("south", {})
            west = vehicle.get("west", {})

            data['nb_forward'] = north.get("forward", 0)
            data['nb_left'] = north.get("turning_left", 0)
            data['nb_right'] = north.get("turning_right", 0)

            data['eb_forward'] = east.get("forward", 0)
            data['eb_left'] = east.get("turning_left", 0)
            data['eb_right'] = east.get("turning_right", 0)

            data['sb_forward'] = south.get("forward", 0)
            data['sb_left'] = south.get("turning_left", 0)
            data['sb_right'] = south.get("turning_right", 0)

            data['wb_forward'] = west.get("forward", 0)
            data['wb_left'] = west.get("turning_left", 0)
            data['wb_right'] = west.get("turning_right", 0)

            junction = json_data.get("junction_settings", {})
            data['lanes'] = junction.get("number_of_lanes", 5)
            data['pedestrian-duration'] = junction.get("pedestrian_duration", 0)
            data['pedestrian-frequency'] = junction.get("pedestrian_frequency", 0)

            tls = json_data.get("traffic_light_settings", {})
            if tls.get("enabled", False):
                data['traffic-light-enable'] = 'on'
            else:
                data['traffic-light-enable'] = ''
            data['tl_sequences'] = tls.get("traffic_cycles", 0)
            vertical_seq = tls.get("vertical_sequence", {})
            horizontal_seq = tls.get("horizontal_sequence", {})
            data['tl_vmain'] = vertical_seq.get("main_green_length", 0)
            data['tl_vright'] = vertical_seq.get("right_green_length", 0)
            data['tl_hmain'] = horizontal_seq.get("main_green_length", 0)
            data['tl_hright'] = horizontal_seq.get("right_green_length") or 0

        elif ext == '.csv':
            file_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(file_content))
            row = next(csv_reader) 

            data['nb_forward'] = row.get("north_forward", 0)
            data['nb_left'] = row.get("north_tleft", 0)
            data['nb_right'] = row.get("north_tright", 0)

            data['eb_forward'] = row.get("east_forward", 0)
            data['eb_left'] = row.get("east_tleft", 0)
            data['eb_right'] = row.get("east_tright", 0)

            data['sb_forward'] = row.get("south_forward", 0)
            data['sb_left'] = row.get("south_tleft", 0)
            data['sb_right'] = row.get("south_tright", 0)

            data['wb_forward'] = row.get("west_forward", 0)
            data['wb_left'] = row.get("west_tleft", 0)
            data['wb_right'] = row.get("west_tright", 0)

            data['lanes'] = row.get("number_of_lanes", 5)
            data['pedestrian-frequency'] = row.get("pedestrian_frequency", 0)
            data['pedestrian-duration'] = row.get("pedestrian_duration", 0)

            if row.get("enable_traffic_light_settings", "").lower() == "true":
                data['traffic-light-enable'] = 'on'
            else:
                data['traffic-light-enable'] = ''
            data['tl_sequences'] = row.get("traffic_cycles", 0)
            data['tl_vmain'] = row.get("vertical_sequence_main_green_length", 0)
            data['tl_vright'] = row.get("vertical_sequence_right_green_length", 0)
            data['tl_hmain'] = row.get("horizontal_sequence_main_green_length", 0)
            data['tl_hright'] = row.get("horizontal_sequence_right_green_length", 0)
    except Exception as e:
        print("Error parsing file:", e)
        return render_template('failure.html')

    print("Parsed file data:", data)

    try:
        session_obj = Session.query.get(global_session_id)

        def safe_int(value):
            try:
                if isinstance(value, str):
                    return int(value.strip()) if value.strip().isdigit() else 0
                return int(value)
            except:
                return 0

        north_vph = safe_int(data.get('nb_forward')) + safe_int(data.get('nb_left')) + safe_int(data.get('nb_right'))
        south_vph = safe_int(data.get('sb_forward')) + safe_int(data.get('sb_left')) + safe_int(data.get('sb_right'))
        east_vph  = safe_int(data.get('eb_forward')) + safe_int(data.get('eb_left')) + safe_int(data.get('eb_right'))
        west_vph  = safe_int(data.get('wb_forward')) + safe_int(data.get('wb_left')) + safe_int(data.get('wb_right'))

        config = Configuration(
            session_id=session_obj.id,
            lanes=safe_int(data.get('lanes', 5)),
            pedestrian_duration=safe_int(data.get('pedestrian-duration')),
            pedestrian_frequency=safe_int(data.get('pedestrian-frequency')),
            north_vph=north_vph,
            north_forward_vph=safe_int(data.get('nb_forward')),
            north_left_vph=safe_int(data.get('nb_left')),
            north_right_vph=safe_int(data.get('nb_right')),
            south_vph=south_vph,
            south_forward_vph=safe_int(data.get('sb_forward')),
            south_left_vph=safe_int(data.get('sb_left')),
            south_right_vph=safe_int(data.get('sb_right')),
            east_vph=east_vph,
            east_forward_vph=safe_int(data.get('eb_forward')),
            east_left_vph=safe_int(data.get('eb_left')),
            east_right_vph=safe_int(data.get('eb_right')),
            west_vph=west_vph,
            west_forward_vph=safe_int(data.get('wb_forward')),
            west_left_vph=safe_int(data.get('wb_left')),
            west_right_vph=safe_int(data.get('wb_right'))
        )
        db.session.add(config)
        db.session.commit()
        print(f"Data stored with run_id {config.run_id}")
        traffic_enabled = data.get('traffic-light-enable', '') == 'on'
        if traffic_enabled:
            tl_config = TrafficSettings(
                run_id=config.run_id,
                session_id=session_obj.id,
                enabled=True,
                sequences_per_hour=safe_int(data.get('tl_sequences')),
                vertical_main_green=safe_int(data.get('tl_vmain')),
                horizontal_main_green=safe_int(data.get('tl_hmain')),
                vertical_right_green=safe_int(data.get('tl_vright')),
                horizontal_right_green=safe_int(data.get('tl_hright'))
            )
        else:
            tl_config = TrafficSettings(
                run_id=config.run_id,
                session_id=session_obj.id,
                enabled=False,
                sequences_per_hour=0,
                vertical_main_green=0,
                horizontal_main_green=0,
                vertical_right_green=0,
                horizontal_right_green=0
            )
        db.session.add(tl_config)
        db.session.commit()
        print(f"Traffic settings stored for run_id {config.run_id}")

        spawn_rates = {
            "north": {
                "forward": safe_int(data.get('nb_forward')),
                "left": safe_int(data.get('nb_left')),
                "right": safe_int(data.get('nb_right'))
            },
            "south": {
                "forward": safe_int(data.get('sb_forward')),
                "left": safe_int(data.get('sb_left')),
                "right": safe_int(data.get('sb_right'))
            },
            "east": {
                "forward": safe_int(data.get('eb_forward')),
                "left": safe_int(data.get('eb_left')),
                "right": safe_int(data.get('eb_right'))
            },
            "west": {
                "forward": safe_int(data.get('wb_forward')),
                "left": safe_int(data.get('wb_left')),
                "right": safe_int(data.get('wb_right'))
            }
        }
        print("Parsed Spawn Rates:", spawn_rates)

        try:
            response = requests.post("http://127.0.0.1:8000/update_spawn_rates", json=spawn_rates)
            if response.status_code == 200:
                print("Spawn rates sent successfully to server.py.")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not reach server.py: {e}")

        junction_settings = {
            "lanes": safe_int(data.get('lanes', 5)),
            "pedestrian_duration": safe_int(data.get('pedestrian-duration')),
            "pedestrian_frequency": safe_int(data.get('pedestrian-frequency'))
        }
        print("Parsed Junction Settings:", junction_settings)


        try:
            response = requests.post("http://127.0.0.1:8000/update_junction_settings", json=junction_settings)
            if response.status_code == 200:
                print("Juncion settings sent succesfully to server.py.")
            else:
                print(f"Error sending juncion settings: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Could not reach server.py: {e}")

        # Construct traffic light settings dictionary
        traffic_light_settings = {
            "traffic-light-enable": "on" if traffic_enabled else "",
            "sequences": safe_int(data.get('tl_sequences')),
            "vertical_main_green": safe_int(data.get('tl_vmain')),
            "horizontal_main_green": safe_int(data.get('tl_hmain')),
            "vertical_right_green": safe_int(data.get('tl_vright')),
            "horizontal_right_green": safe_int(data.get('tl_hright'))
        }
        try:
            response = requests.post("http://127.0.0.1:8000/update_traffic_light_settings", json=traffic_light_settings)
            if response.status_code == 200:
                print("Traffic light settings sent successfully to server.py.")
            else:
                print(f"Error sending traffic light settings: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Could not reach server.py for trafic lights: {e}")

        print("THIS IS DEBUG" + str(safe_int(data.get('lanes', 5))))

        return jsonify({
            "redirect_url": url_for('junctionPage'),
            "lanes": safe_int(data.get('lanes', 5))
            })

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 400




def simulate():
    """
    Simulate a traffic run and save the simulation results.

    Retrieves simulation parameters (run_id and session_id) from the request JSON, then sends a GET request
    to the fastapi simulation endpoint. Then proceses the simulation response to extract user and algorithm metrics, 
    calculates scores and saves leaderboard results 
    
    Returns:
        Response: A response containing simulation results and calculated scores,
                  or an error message with a 400 status code.
    """
    
    try:
    
        data = request.json
        run_id = data.get('run_id')
        session_id = data.get('session_id')
        
        sim_response = requests.get("https://junction-simulator.onrender.com/simulate_fast")
        sim_response.raise_for_status()  
        
        metrics = sim_response.json()

        user_metrics = metrics["user"]
        algorithm_metrics = metrics["default"]
        
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
            run_id,
            session_id,
            user_metrics["avg_wait_time_n"], user_metrics["max_wait_time_n"], user_metrics["max_queue_length_n"],
            user_metrics["avg_wait_time_s"], user_metrics["max_wait_time_s"], user_metrics["max_queue_length_s"],
            user_metrics["avg_wait_time_e"], user_metrics["max_wait_time_e"], user_metrics["max_queue_length_e"],
            user_metrics["avg_wait_time_w"], user_metrics["max_wait_time_w"], user_metrics["max_queue_length_w"], 
        )
        
        default_score = compute_score_4directions(
            run_id,
            session_id,
            algorithm_metrics["avg_wait_time_n"], algorithm_metrics["max_wait_time_n"], algorithm_metrics["max_queue_length_n"],
            algorithm_metrics["avg_wait_time_s"], algorithm_metrics["max_wait_time_s"], algorithm_metrics["max_queue_length_s"],
            algorithm_metrics["avg_wait_time_e"], algorithm_metrics["max_wait_time_e"], algorithm_metrics["max_queue_length_e"],
            algorithm_metrics["avg_wait_time_w"], algorithm_metrics["max_wait_time_w"], algorithm_metrics["max_queue_length_w"],
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
    Render the junction page.

    Returns:
       Renders the page for the junction view.
    """
    
    return render_template('junctionPage.html')

@app.route('/leaderboards')
def leaderboards():
    """
    Render the leaderboards page with all time best configurations.

    Returns:
        Renders the page for leaderboards with the top results.
    """
    
    results = get_all_time_best_configurations()

    print(results)
    
    return render_template('leaderboards.html', results=results)


def get_all_time_best_configurations():
    """
    Gets and calcuates the all-time best configurations from the leaderboard.

    The function joins leaderboard results with algorithm results and trafic settings,
    computes scores, and returns the top 10 configuraions based on the score difference.

    Returns:
        list: A list of dictionaries containing configuration details and scores.
    """
    
    results = db.session.query(LeaderboardResult, AlgorithmLeaderboardResult) \
    .join(
        AlgorithmLeaderboardResult,
        and_(
            LeaderboardResult.run_id == AlgorithmLeaderboardResult.run_id,
            LeaderboardResult.session_id == AlgorithmLeaderboardResult.session_id
        )
    ) \
    .join(
        TrafficSettings,
        and_(
            LeaderboardResult.run_id == TrafficSettings.run_id,
            LeaderboardResult.session_id == TrafficSettings.session_id
        )
    ) \
    .filter(TrafficSettings.enabled == True) \
    .all()

    results_with_scores = []

    for ur, ar in results:
        user_score = compute_score_4directions(
            ur.run_id,
            ur.session_id,
            ur.avg_wait_time_north, ur.max_wait_time_north, ur.max_queue_length_north,
            ur.avg_wait_time_south, ur.max_wait_time_south, ur.max_queue_length_south,
            ur.avg_wait_time_east, ur.max_wait_time_east, ur.max_queue_length_east,
            ur.avg_wait_time_west, ur.max_wait_time_west, ur.max_queue_length_west
        )

        algorithm_score = compute_score_4directions(
            ar.run_id,
            ar.session_id,
            ar.avg_wait_time_north, ar.max_wait_time_north, ar.max_queue_length_north,
            ar.avg_wait_time_south, ar.max_wait_time_south, ar.max_queue_length_south,
            ar.avg_wait_time_east, ar.max_wait_time_east, ar.max_queue_length_east,
            ar.avg_wait_time_west, ar.max_wait_time_west, ar.max_queue_length_west
        )

        score_difference = algorithm_score - user_score

        result_data = {
            "run_id": ur.run_id,
            "session_id": ur.session_id,
            "user_score": user_score,
            "algorithm_score": algorithm_score,
            "score_difference": score_difference,
            "avg_wait_time_north": ur.avg_wait_time_north,
            "max_wait_time_north": ur.max_wait_time_north,
            "max_queue_length_north": ur.max_queue_length_north,
            "avg_wait_time_south": ur.avg_wait_time_south,
            "max_wait_time_south": ur.max_wait_time_south,
            "max_queue_length_south": ur.max_queue_length_south,
            "avg_wait_time_east": ur.avg_wait_time_east,
            "max_wait_time_east": ur.max_wait_time_east,
            "max_queue_length_east": ur.max_queue_length_east,
            "avg_wait_time_west": ur.avg_wait_time_west,
            "max_wait_time_west": ur.max_wait_time_west,
            "max_queue_length_west": ur.max_queue_length_west,
        }

        results_with_scores.append(result_data)

    results_with_scores.sort(key=lambda x: x["score_difference"], reverse=True)

    return results_with_scores[:10]


@app.route('/session_leaderboard')
def session_leaderboard_page():
    """
    Render the session leaderboard page.

    Determines the current session and retrieves the recent runs with computed scores,
    then renders the leaderbaord page for that session.

    Returns:
        Renders page for session leaderboard.
    """
    
    session_id = request.args.get('session_id', type=int)
    
    if not session_id:
        active_session = Session.query.filter_by(active=True).order_by(Session.id.desc()).first()
        session_id = active_session.id if active_session else None
    
    runs = get_recent_runs_with_scores(session_id) if session_id else []

    print(get_all_time_best_configurations())
    
    return render_template('session_leaderboard.html', runs=runs, session_id=session_id)

def get_recent_algorithm_runs(session_id):
    """
    Retrieve the most recent algorithm leaderboard runs for a given session.

    Args:
        session_id (int): To identify the session.

    Returns:
        list: A list of recent algorithm leaderboard runs.
    """
    return AlgorithmLeaderboardResult.query \
        .filter_by(session_id=session_id) \
        .order_by(AlgorithmLeaderboardResult.id.desc()) \
        .limit(10) \
        .all()

@app.route('/algorithm_session_leaderboard')
def algorithm_session_leaderboard_page():
    """
    Render the algorithm session leaderboard page.

    Retrieves recent algorithm runs for the given session, computes scores for each run,
    and renders the leaderboard page.

    Returns:
        Renders HTML page for algorithm session leaderboard.
    """

    session_id = request.args.get('session_id', type=int)
    
    if not session_id:
        active_session = Session.query.filter_by(active=True).order_by(Session.id.desc()).first()
        session_id = active_session.id if active_session else None

    print(session_id)
    
    raw_runs = get_recent_algorithm_runs(session_id) if session_id else []
    
    processed_runs = []
    for run in raw_runs:
        score = compute_score_4directions(
            run.run_id,
            run.session_id,
            run.avg_wait_time_north, run.max_wait_time_north, run.max_queue_length_north,
            run.avg_wait_time_south, run.max_wait_time_south, run.max_queue_length_south,
            run.avg_wait_time_east, run.max_wait_time_east, run.max_queue_length_east,
            run.avg_wait_time_west, run.max_wait_time_west, run.max_queue_length_west
        )
        processed_runs.append({
            "run_id": run.run_id,
            "nb_avg_wait": run.avg_wait_time_north,
            "nb_max_wait": run.max_wait_time_north,
            "nb_max_queue": run.max_queue_length_north,
            "sb_avg_wait": run.avg_wait_time_south,
            "sb_max_wait": run.max_wait_time_south,
            "sb_max_queue": run.max_queue_length_south,
            "eb_avg_wait": run.avg_wait_time_east,
            "eb_max_wait": run.max_wait_time_east,
            "eb_max_queue": run.max_queue_length_east,
            "wb_avg_wait": run.avg_wait_time_west,
            "wb_max_wait": run.max_wait_time_west,
            "wb_max_queue": run.max_queue_length_west,
            "score": score
        })
    
    return render_template('algorithm_session_leaderboard.html', runs=processed_runs, session_id=session_id)



@app.route('/simulate', methods=['POST'])
def simulate_endpoint():
    """
    Endpoint to simulate the process.
    Returns:
        The response from the simulate() function.
    """
    return simulate()


def compute_score_4directions(
    run_id,
    session_id,
    nb_avg, nb_max, nb_queue,
    sb_avg, sb_max, sb_queue,
    eb_avg, eb_max, eb_queue,
    wb_avg, wb_max, wb_queue,
):
    """
    Compute a combined score for four directions based on various traffic metrics.

    The score is computed for each direction (north, south, east, west) using the
    weighted sum of average wait time, maximum wait time, and maximum queue length, normalised
    by the total vehicle volume for that direction. The final score is the sum of the four
    directional scores.

    Args:
        run_id (int): The run identifier.
        session_id (int): The session identifier.
        nb_avg (float): Average wait time for northbound.
        nb_max (float): Maximum wait time for northbound.
        nb_queue (int): Maximum queue length for northbound.
        sb_avg (float): Average wait time for southbound.
        sb_max (float): Maximum wait time for southbound.
        sb_queue (int): Maximum queue length for southbound.
        eb_avg (float): Average wait time for eastbound.
        eb_max (float): Maximum wait time for eastbound.
        eb_queue (int): Maximum queue length for eastbound.
        wb_avg (float): Average wait time for westbound.
        wb_max (float): Maximum wait time for westbound.
        wb_queue (int): Maximum queue length for westbound.

    Returns:
        float: The calculated total score.
    """

    vehicle_input = Configuration.query.filter_by(run_id=run_id, session_id=session_id).first()

    if not vehicle_input:
        raise ValueError("Configuration not found for provided run and session ID.")

    north_total = (vehicle_input.north_forward_vph + 
                   vehicle_input.north_left_vph + 
                   vehicle_input.north_right_vph)

    south_total = (vehicle_input.south_forward_vph + 
                   vehicle_input.south_left_vph + 
                   vehicle_input.south_right_vph)

    east_total = (vehicle_input.east_forward_vph + 
                  vehicle_input.east_left_vph + 
                  vehicle_input.east_right_vph)

    west_total = (vehicle_input.west_forward_vph + 
                  vehicle_input.west_left_vph + 
                  vehicle_input.west_right_vph)
    
    def directional_score(avg, max_w, queue, volume):
        """
        Calculate the directional score based on weighted metrics.

        Args:
            avg (float): Average wait time.
            max_w (float): Maximum wait time.
            queue (int): Maximum queue length.
            volume (int): Total vehicle volume in the direction.

        Returns:
            float: The computed directional score.
        """
        if volume == 0:
            return 0

        weighted_score = (0.45 * avg) + (0.2 * max_w) + (0.35 * queue)

        return weighted_score / volume

    nb_score = directional_score(nb_avg, nb_max, nb_queue, north_total)
    sb_score = directional_score(sb_avg, sb_max, sb_queue, south_total)
    eb_score = directional_score(eb_avg, eb_max, eb_queue, east_total)
    wb_score = directional_score(wb_avg, wb_max, wb_queue, west_total)

    total_score = nb_score + sb_score + eb_score + wb_score

    return total_score

def get_recent_runs_with_scores(session_id):
    """
    Retrieve the recent runs for a session with user and algorithm scores.

    Joins leaderboard and algorithm results, computes the score difference for each run,
    and returns a sorted list of runs.

    Args:
        session_id (int): To identify the session.

    Returns:
        list: A list of dictionaries containing run details and scores.
    """
    
    recent_runs = (
        LeaderboardResult.query
        .join(TrafficSettings, LeaderboardResult.run_id == TrafficSettings.run_id)
        .filter(LeaderboardResult.session_id == session_id, TrafficSettings.enabled == True)
        .order_by(LeaderboardResult.run_id.desc())
        .limit(10)
        .all(),
        AlgorithmLeaderboardResult.query
        .join(TrafficSettings, AlgorithmLeaderboardResult.run_id == TrafficSettings.run_id)
        .filter(AlgorithmLeaderboardResult.session_id == session_id, TrafficSettings.enabled == True)
        .order_by(AlgorithmLeaderboardResult.run_id.desc())
        .limit(10)
        .all()
    )

    
    runs_with_scores = []

    leaderboard_results, algorithm_leaderboard_results = recent_runs

    for ur, ar in zip(leaderboard_results, algorithm_leaderboard_results):

        user_final_score = compute_score_4directions(
            ur.run_id,
            ur.session_id,
            ur.avg_wait_time_north, ur.max_wait_time_north, ur.max_queue_length_north,
            ur.avg_wait_time_south, ur.max_wait_time_south, ur.max_queue_length_south,
            ur.avg_wait_time_east,  ur.max_wait_time_east,  ur.max_queue_length_east,
            ur.avg_wait_time_west,  ur.max_wait_time_west,  ur.max_queue_length_west,
        )

        algorithm_final_score = compute_score_4directions(
            ar.run_id,
            ar.session_id,
            ar.avg_wait_time_north, ar.max_wait_time_north, ar.max_queue_length_north,
            ar.avg_wait_time_south, ar.max_wait_time_south, ar.max_queue_length_south,
            ar.avg_wait_time_east,  ar.max_wait_time_east,  ar.max_queue_length_east,
            ar.avg_wait_time_west,  ar.max_wait_time_west,  ar.max_queue_length_west,
        )

        final_score = algorithm_final_score - user_final_score

        runs_with_scores.append({
            "run_id": ur.run_id,

            "nb_avg_wait": ur.avg_wait_time_north,
            "nb_max_wait": ur.max_wait_time_north,
            "nb_max_queue": ur.max_queue_length_north,

            "sb_avg_wait": ur.avg_wait_time_south,
            "sb_max_wait": ur.max_wait_time_south,
            "sb_max_queue": ur.max_queue_length_south,

            "eb_avg_wait": ur.avg_wait_time_east,
            "eb_max_wait": ur.max_wait_time_east,
            "eb_max_queue": ur.max_queue_length_east,

            "wb_avg_wait": ur.avg_wait_time_west,
            "wb_max_wait": ur.max_wait_time_west,
            "wb_max_queue": ur.max_queue_length_west,

            "user_score": user_final_score,
            "algorithm_score": algorithm_final_score,

            "score": final_score
        })

    if not runs_with_scores:
        return []

    best_run = max(runs_with_scores, key=lambda x: x["score"])

    runs_with_scores.remove(best_run)

    runs_with_scores.sort(key=lambda x: x["run_id"], reverse=True)
    
    final_list = [best_run] + runs_with_scores

    return final_list

@app.route('/junction_details', methods=['GET'])
def junction_details():
    """
    Render the junction details page with configuration, traffic settings, and scores.

    Retrieves the config, traffic settings, and leaderboard results (both user and algorithm)
    for a given run and session, computes score differences, and renders the junction details page.

    Returns:
        A rendered HTML page with detailed junction information.
    """
    # Get run_id and session_id from query parameters.
    session_id = request.args.get('session_id', type=int)
    run_id = request.args.get('run_id', type=int)

    if not session_id:
        return redirect(url_for('error', message="No session ID provided."))

    if not run_id:
        return redirect(url_for('error', message="No run ID provided."))

    # Query configuration based on run_id and session_id.
    if session_id:
        configuration = Configuration.query.filter_by(run_id=run_id, session_id=session_id).first()

    if not configuration:
        flash('Configuration details not found for the provided run.')
        return redirect(url_for('error', message=f"Configuration for Run: {str(run_id)} in Session: {str(session_id)} does not exist."))
    
    session_id = configuration.session_id

    # Query traffic settings.
    if session_id:
        tls_obj = TrafficSettings.query.filter_by(run_id=run_id, session_id=session_id).first()
    else:
        tls_obj = TrafficSettings.query.filter_by(run_id=run_id).first()
    if not tls_obj:
        traffic_light_settings = {
            "enabled": False,
            "sequences_per_hour": 0,
            "vertical_main_green": 0,
            "horizontal_main_green": 0,
            "vertical_right_green": 0,
            "horizontal_right_green": 0
        }
    else:
        traffic_light_settings = {
            "enabled": tls_obj.enabled,
            "sequences_per_hour": tls_obj.sequences_per_hour,
            "vertical_main_green": tls_obj.vertical_main_green,
            "horizontal_main_green": tls_obj.horizontal_main_green,
            "vertical_right_green": tls_obj.vertical_right_green,
            "horizontal_right_green": tls_obj.horizontal_right_green
        }

    # Query user leaderboard result.
    user_result = LeaderboardResult.query.filter_by(run_id=run_id, session_id=session_id).first()
    if user_result:
        user_metrics = {
            "avg_wait_time_n": user_result.avg_wait_time_north,
            "avg_wait_time_s": user_result.avg_wait_time_south,
            "avg_wait_time_e": user_result.avg_wait_time_east,
            "avg_wait_time_w": user_result.avg_wait_time_west,
            "max_wait_time_n": user_result.max_wait_time_north,
            "max_wait_time_s": user_result.max_wait_time_south,
            "max_wait_time_e": user_result.max_wait_time_east,
            "max_wait_time_w": user_result.max_wait_time_west,
            "max_queue_length_n": user_result.max_queue_length_north,
            "max_queue_length_s": user_result.max_queue_length_south,
            "max_queue_length_e": user_result.max_queue_length_east,
            "max_queue_length_w": user_result.max_queue_length_west,
        }
        user_metrics["score"] = compute_score_4directions(
            run_id,
            session_id,
            user_metrics["avg_wait_time_n"],
            user_metrics["max_wait_time_n"],
            user_metrics["max_queue_length_n"],
            user_metrics["avg_wait_time_s"],
            user_metrics["max_wait_time_s"],
            user_metrics["max_queue_length_s"],
            user_metrics["avg_wait_time_e"],
            user_metrics["max_wait_time_e"],
            user_metrics["max_queue_length_e"],
            user_metrics["avg_wait_time_w"],
            user_metrics["max_wait_time_w"],
            user_metrics["max_queue_length_w"]
        )
    else:
        user_metrics = {
            "avg_wait_time_n": 0, "avg_wait_time_s": 0, "avg_wait_time_e": 0, "avg_wait_time_w": 0,
            "max_wait_time_n": 0, "max_wait_time_s": 0, "max_wait_time_e": 0, "max_wait_time_w": 0,
            "max_queue_length_n": 0, "max_queue_length_s": 0, "max_queue_length_e": 0, "max_queue_length_w": 0,
            "score": 0.0
        }

    # Query algorithm leaderboard result.
    algo_result = AlgorithmLeaderboardResult.query.filter_by(run_id=run_id, session_id=session_id).first()
    if algo_result:
        algorithm_metrics = {
            "avg_wait_time_n": algo_result.avg_wait_time_north,
            "avg_wait_time_s": algo_result.avg_wait_time_south,
            "avg_wait_time_e": algo_result.avg_wait_time_east,
            "avg_wait_time_w": algo_result.avg_wait_time_west,
            "max_wait_time_n": algo_result.max_wait_time_north,
            "max_wait_time_s": algo_result.max_wait_time_south,
            "max_wait_time_e": algo_result.max_wait_time_east,
            "max_wait_time_w": algo_result.max_wait_time_west,
            "max_queue_length_n": algo_result.max_queue_length_north,
            "max_queue_length_s": algo_result.max_queue_length_south,
            "max_queue_length_e": algo_result.max_queue_length_east,
            "max_queue_length_w": algo_result.max_queue_length_west,
        }
        algorithm_metrics["score"] = compute_score_4directions(
            run_id,
            session_id,
            algorithm_metrics["avg_wait_time_n"],
            algorithm_metrics["max_wait_time_n"],
            algorithm_metrics["max_queue_length_n"],
            algorithm_metrics["avg_wait_time_s"],
            algorithm_metrics["max_wait_time_s"],
            algorithm_metrics["max_queue_length_s"],
            algorithm_metrics["avg_wait_time_e"],
            algorithm_metrics["max_wait_time_e"],
            algorithm_metrics["max_queue_length_e"],
            algorithm_metrics["avg_wait_time_w"],
            algorithm_metrics["max_wait_time_w"],
            algorithm_metrics["max_queue_length_w"]
        )
    else:
        algorithm_metrics = {
            "avg_wait_time_n": 0, "avg_wait_time_s": 0, "avg_wait_time_e": 0, "avg_wait_time_w": 0,
            "max_wait_time_n": 0, "max_wait_time_s": 0, "max_wait_time_e": 0, "max_wait_time_w": 0,
            "max_queue_length_n": 0, "max_queue_length_s": 0, "max_queue_length_e": 0, "max_queue_length_w": 0,
            "score": 0.0
        }

    score_diff = algorithm_metrics["score"] - user_metrics["score"]

    return render_template(
        'junction_details.html',
        configuration=configuration,
        traffic_light_settings=traffic_light_settings,
        user_metrics=user_metrics,
        algorithm_metrics=algorithm_metrics,
        score_diff=score_diff
    )

@app.route('/error')
def error():
    """
    Render the search page for algorithm runs.

    Returns:
        A rendered HTML page for searching algorithm runs.
    """
    message = request.args.get('message', 'An unknown error occurred. Please try again.')

    return render_template('error.html', error_message=message)


@app.route('/search_Algorithm_Runs', methods=['GET'])
def search_algorithm_runs():
    return render_template('search_Algorithm_Runs.html')


@app.route('/download_metrics_json')
def download_metrics_json():
    """"
    Generate and download metrics as a JSON file.

    Computes scores for each record, and returns a 
    JSON response with one JSON object per line.

    Returns:
        A Flask Response object containing the metrics in JSON format.
    """
    results = db.session.query(LeaderboardResult, AlgorithmLeaderboardResult).join(
        AlgorithmLeaderboardResult,
        LeaderboardResult.run_id == AlgorithmLeaderboardResult.run_id
    ).all()

    lines = []
    for ur, ar in results:
        user_score = compute_score_4directions(
            ur.run_id,
            ur.session_id,
            ur.avg_wait_time_north, ur.max_wait_time_north, ur.max_queue_length_north,
            ur.avg_wait_time_south, ur.max_wait_time_south, ur.max_queue_length_south,
            ur.avg_wait_time_east,  ur.max_wait_time_east,  ur.max_queue_length_east,
            ur.avg_wait_time_west, ur.max_wait_time_west, ur.max_queue_length_west,
        )
        algo_score = compute_score_4directions(
            ar.run_id,
            ar.session_id,
            ar.avg_wait_time_north, ar.max_wait_time_north, ar.max_queue_length_north,
            ar.avg_wait_time_south, ar.max_wait_time_south, ar.max_queue_length_south,
            ar.avg_wait_time_east, ar.max_wait_time_east, ar.max_queue_length_east,
            ar.avg_wait_time_west, ar.max_wait_time_west, ar.max_queue_length_west,
        )
        score = algo_score - user_score

        # If traffic is disabled, skip user_score or set it to None, etc.
        # For now, we include user_score for demonstration.
        record = {
            "run_id": ur.run_id,
            "session_id": ur.session_id,
            "user_score": user_score,
            "algo_score": algo_score,
            "score_diff": score
        }
        lines.append(json.dumps(record))
    content = "\n".join(lines)

    return Response(
        content,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=metrics.json"}
    )

@app.route('/loading')
def loading():
    """
    Render the loading page.

    Returns:
        A rendered HTML page for the loading screen.
    """
    return render_template('loading.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)