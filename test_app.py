import io
import json
import csv
import pytest
from flask import jsonify
from sqlalchemy.pool import StaticPool
from app import app, db, create_session, end_session, compute_score_4directions, process_csv, get_latest_spawn_rates, get_latest_junction_settings, get_latest_traffic_light_settings, simulate
from models import (
    Configuration, Session, TrafficSettings,
    LeaderboardResult, AlgorithmLeaderboardResult
)

# --- DummyResponse for monkeypatching external HTTP calls ---
class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
    def json(self):
        return self._json
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("HTTP error")

# --- Helper: create a full Configuration record ---
def create_full_configuration(session_id, run_id=1, lanes=3, p_duration=10, p_frequency=5, traffic=10):
    # For each direction, assume forward, left, and right each equal to 'traffic'
    forward = traffic
    left = traffic
    right = traffic
    total = forward + left + right  # e.g., 10+10+10 = 30
    return Configuration(
        session_id=session_id,
        run_id=run_id,
        lanes=lanes,
        left_turn_lane=True,
        pedestrian_duration=p_duration,
        pedestrian_frequency=p_frequency,
        north_vph=total,
        north_forward_vph=forward,
        north_left_vph=left,
        north_right_vph=right,
        south_vph=total,
        south_forward_vph=forward,
        south_left_vph=left,
        south_right_vph=right,
        east_vph=total,
        east_forward_vph=forward,
        east_left_vph=left,
        east_right_vph=right,
        west_vph=total,
        west_forward_vph=forward,
        west_left_vph=left,
        west_right_vph=right
    )

# --- Pytest fixture for the Flask test client with an in-memory database ---
@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Use an in-memory SQLite database with a static pool to persist across connections.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool
    }
    with app.app_context():
        db.create_all()
        # Create a dummy session and update the module-level global session id.
        s = create_session()
        app.global_session_id = s  # s is an integer (session id)
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()

# =========================
# Simulation Endpoints Tests
# =========================

def test_start_simulation(client, monkeypatch):
    monkeypatch.setattr("app.start_fastapi", lambda: None)
    response = client.post("/start_simulation")
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "FastAPI server started"

def test_stop_simulation(client, monkeypatch):
    monkeypatch.setattr("app.stop_fastapi", lambda: None)
    response = client.post("/stop_simulation")
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "FastAPI server stopped"

def test_back_to_parameters(client, monkeypatch):
    monkeypatch.setattr("app.stop_fastapi", lambda: None)
    response = client.get("/back_to_parameters", follow_redirects=False)
    assert response.status_code in (301, 302)
    location = response.headers.get("Location")
    assert "/parameters" in location

# =========================
# Helper Function Tests
# =========================

def test_get_latest_spawn_rates(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        db.session.commit()
        rates = get_latest_spawn_rates()
        assert rates["north"]["forward"] == 10

def test_get_latest_junction_settings(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        # Create configuration with lanes set to 4.
        config = create_full_configuration(session_id=s.id, run_id=1, lanes=4, p_duration=10, p_frequency=5)
        db.session.add(config)
        db.session.commit()
        settings = get_latest_junction_settings()
        assert settings["lanes"] == 4
        assert settings["pedestrian_duration"] == 10

def test_get_latest_traffic_light_settings(client):
    with app.app_context():
        ts = get_latest_traffic_light_settings()
        assert ts["enabled"] is False

def test_process_csv():
    csv_content = (
        "pedestrian_duration,pedestrian_frequency,north_forward_vph,north_left_vph,north_right_vph,"
        "south_forward_vph,south_left_vph,south_right_vph,east_forward_vph,east_left_vph,east_right_vph,"
        "west_forward_vph,west_left_vph,west_right_vph\n"
        "10,5,5,3,2,4,4,1,6,2,3,7,3,4\n"
    )
    class DummyFile:
        def __init__(self, content):
            self.stream = io.BytesIO(content.encode("utf-8"))
    dummy_file = DummyFile(csv_content)
    configs = process_csv(dummy_file)
    assert len(configs) == 1
    config = configs[0]
    assert config.pedestrian_duration == "10"

# =========================
# Session and Index Endpoints Tests
# =========================

def test_start_session_api(client):
    response = client.post("/start_session")
    data = response.get_json()
    assert response.status_code == 200
    assert "session_id" in data
    assert data["message"] == "Session started"

def test_end_session_api(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        sid = s.id
    response = client.post("/end_session", json={"session_id": sid})
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "Session ended"

def test_index_and_indexTwo(client):
    response1 = client.get("/")
    response2 = client.get("/index")
    assert response1.status_code == 200
    assert response2.status_code == 200

def test_get_session_run_id_endpoint(client):
    with app.app_context():
        s = Session(active=True)
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=10)
        db.session.add(config)
        db.session.commit()
    response = client.get("/get_session_run_id")
    data = response.get_json()
    assert response.status_code == 200
    assert "session_id" in data
    assert "run_id" in data
    assert data["run_id"] == 10

# =========================
# Results, Simulation, and Junction Endpoints Tests
# =========================

def test_results_endpoint(client, monkeypatch):
    with app.app_context():
        s = Session(active=True)
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        db.session.commit()
    dummy_sim = lambda: (jsonify({
        "user": {
            "avg_wait_time_n": 10, "max_wait_time_n": 15, "max_queue_length_n": 5,
            "avg_wait_time_s": 10, "max_wait_time_s": 15, "max_queue_length_s": 5,
            "avg_wait_time_e": 10, "max_wait_time_e": 15, "max_queue_length_e": 5,
            "avg_wait_time_w": 10, "max_wait_time_w": 15, "max_queue_length_w": 5,
            "score": 1.0
        },
        "default": {
            "avg_wait_time_n": 12, "max_wait_time_n": 18, "max_queue_length_n": 6,
            "avg_wait_time_s": 12, "max_wait_time_s": 18, "max_queue_length_s": 6,
            "avg_wait_time_e": 12, "max_wait_time_e": 18, "max_queue_length_e": 6,
            "avg_wait_time_w": 12, "max_wait_time_w": 18, "max_queue_length_w": 6,
            "score": 1.5
        }
    }), 200)
    monkeypatch.setattr("app.simulate", dummy_sim)
    with app.app_context():
        s2 = create_session()
        app.global_session_id = s2
    response = client.get("/results?session_id={}&run_id=1".format(app.global_session_id))
    assert response.status_code == 200

def test_back_to_results_endpoint(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        ts = TrafficSettings(
            run_id=1, session_id=s.id, enabled=True,
            sequences_per_hour=10, vertical_main_green=30,
            horizontal_main_green=30, vertical_right_green=10, horizontal_right_green=10
        )
        db.session.add(ts)
        lb = LeaderboardResult(
            session_id=s.id, run_id=1,
            avg_wait_time_north=10, max_wait_time_north=15, max_queue_length_north=5,
            avg_wait_time_south=10, max_wait_time_south=15, max_queue_length_south=5,
            avg_wait_time_east=10, max_wait_time_east=15, max_queue_length_east=5,
            avg_wait_time_west=10, max_wait_time_west=15, max_queue_length_west=5
        )
        db.session.add(lb)
        db.session.commit()
        sid = s.id
    response = client.get("/back_to_results?session_id={}&run_id=1".format(sid))
    assert response.status_code in (200, 302)

def test_simulate_endpoint(client, monkeypatch):
    def dummy_requests_get(url, *args, **kwargs):
        data = {
            "user": {
                "avg_wait_time_n": 10, "max_wait_time_n": 15, "max_queue_length_n": 5,
                "avg_wait_time_s": 10, "max_wait_time_s": 15, "max_queue_length_s": 5,
                "avg_wait_time_e": 10, "max_wait_time_e": 15, "max_queue_length_e": 5,
                "avg_wait_time_w": 10, "max_wait_time_w": 15, "max_queue_length_w": 5
            },
            "default": {
                "avg_wait_time_n": 12, "max_wait_time_n": 18, "max_queue_length_n": 6,
                "avg_wait_time_s": 12, "max_wait_time_s": 18, "max_queue_length_s": 6,
                "avg_wait_time_e": 12, "max_wait_time_e": 18, "max_queue_length_e": 6,
                "avg_wait_time_w": 12, "max_wait_time_w": 18, "max_queue_length_w": 6
            }
        }
        return DummyResponse(data, 200)
    monkeypatch.setattr("app.requests.get", dummy_requests_get)
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        db.session.commit()
        app.global_session_id = s.id
    payload = {"run_id": 1, "session_id": app.global_session_id}
    response = client.post("/simulate", json=payload)
    data = response.get_json()
    assert response.status_code == 201
    assert "message" in data
    assert "user" in data
    assert "default" in data

def test_junction_details_endpoint(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        ts = TrafficSettings(
            run_id=1, session_id=s.id, enabled=True,
            sequences_per_hour=10, vertical_main_green=30,
            horizontal_main_green=30, vertical_right_green=10, horizontal_right_green=10
        )
        db.session.add(ts)
        lb = LeaderboardResult(
            session_id=s.id, run_id=1,
            avg_wait_time_north=10, max_wait_time_north=15, max_queue_length_north=5,
            avg_wait_time_south=10, max_wait_time_south=15, max_queue_length_south=5,
            avg_wait_time_east=10, max_wait_time_east=15, max_queue_length_east=5,
            avg_wait_time_west=10, max_wait_time_west=15, max_queue_length_west=5
        )
        db.session.add(lb)
        db.session.commit()
        sid = s.id
    query_string = f"?session_id={sid}&run_id=1"
    response = client.get("/junction_details" + query_string, follow_redirects=True)
    assert response.status_code == 200

# =========================
# Parameters, Upload, and Proxy Endpoints Tests
# =========================

def test_parameters_get(client):
    response = client.get("/parameters")
    assert response.status_code == 200

def test_junction_settings_proxy(client, monkeypatch):
    dummy_data = {"lanes": 3, "pedestrian_duration": 10, "pedestrian_frequency": 5}
    monkeypatch.setattr("app.requests.get", lambda url: DummyResponse(dummy_data, 200))
    response = client.get("/junction_settings_proxy")
    data = response.get_json()
    assert response.status_code == 200
    assert data["lanes"] == 3

def test_upload_file_endpoint(client):
    data = {"file": (io.BytesIO(b"dummy content"), "test.txt")}
    response = client.post("/upload-file", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert "uploaded successfully" in response.get_data(as_text=True)

# =========================
# Other Page Endpoints Tests
# =========================

def test_junctionPage(client):
    response = client.get("/junctionPage")
    assert response.status_code == 200

def test_leaderboards_page(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        lb = LeaderboardResult(
            session_id=s.id, run_id=1,
            avg_wait_time_north=10, max_wait_time_north=15, max_queue_length_north=5,
            avg_wait_time_south=10, max_wait_time_south=15, max_queue_length_south=5,
            avg_wait_time_east=10, max_wait_time_east=15, max_queue_length_east=5,
            avg_wait_time_west=10, max_wait_time_west=15, max_queue_length_west=5
        )
        algo = AlgorithmLeaderboardResult(
            session_id=s.id, run_id=1,
            avg_wait_time_north=12, max_wait_time_north=18, max_queue_length_north=6,
            avg_wait_time_south=12, max_wait_time_south=18, max_queue_length_south=6,
            avg_wait_time_east=12, max_wait_time_east=18, max_queue_length_east=6,
            avg_wait_time_west=12, max_wait_time_west=18, max_queue_length_west=6
        )
        ts = TrafficSettings(
            run_id=1, session_id=s.id, enabled=True,
            sequences_per_hour=10, vertical_main_green=30,
            horizontal_main_green=30, vertical_right_green=10, horizontal_right_green=10
        )
        db.session.add_all([lb, algo, ts])
        db.session.commit()
    response = client.get("/leaderboards")
    assert response.status_code == 200

def test_session_leaderboard_page(client):
    response = client.get("/session_leaderboard?session_id=1")
    assert response.status_code == 200

def test_algorithm_session_leaderboard_page(client):
    response = client.get("/algorithm_session_leaderboard?session_id=1")
    assert response.status_code == 200

def test_search_algorithm_runs_page(client):
    response = client.get("/search_Algorithm_Runs")
    assert response.status_code == 200

def test_download_metrics_json_endpoint(client):
    with app.app_context():
        s = Session()
        db.session.add(s)
        db.session.commit()
        config = create_full_configuration(session_id=s.id, run_id=1)
        db.session.add(config)
        lb = LeaderboardResult(
            session_id=s.id, run_id=1,
            avg_wait_time_north=10, max_wait_time_north=15, max_queue_length_north=5,
            avg_wait_time_south=10, max_wait_time_south=15, max_queue_length_south=5,
            avg_wait_time_east=10, max_wait_time_east=15, max_queue_length_east=5,
            avg_wait_time_west=10, max_wait_time_west=15, max_queue_length_west=5
        )
        algo = AlgorithmLeaderboardResult(
            session_id=s.id, run_id=1,
            avg_wait_time_north=12, max_wait_time_north=18, max_queue_length_north=6,
            avg_wait_time_south=12, max_wait_time_south=18, max_queue_length_south=6,
            avg_wait_time_east=12, max_wait_time_east=18, max_queue_length_east=6,
            avg_wait_time_west=12, max_wait_time_west=18, max_queue_length_west=6
        )
        ts = TrafficSettings(
            run_id=1, session_id=s.id, enabled=True,
            sequences_per_hour=10, vertical_main_green=30,
            horizontal_main_green=30, vertical_right_green=10, horizontal_right_green=10
        )
        db.session.add_all([lb, algo, ts])
        db.session.commit()
    response = client.get("/download_metrics_json")
    assert response.status_code == 200
    content_disp = response.headers.get("Content-Disposition")
    assert "attachment;filename=metrics.json" in content_disp

def test_loading_page(client):
    response = client.get("/loading")
    assert response.status_code == 200

def test_error_page(client):
    response = client.get("/error?message=Test+error")
    assert response.status_code == 200
    assert "Test error" in response.get_data(as_text=True)
