import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from models import db, Configuration, LeaderboardResult, Session, TrafficSettings

# Import your Flask app, db, and any functions you want to test
# Adjust if your main file is named differently, e.g. `from main import app`
from app import app, db, create_session, end_session, process_csv, simulate, compute_score_4directions

@pytest.fixture
def client():
    """
    This fixture creates a fresh in-memory database for each test
    and returns a Flask test client to send requests to your routes.
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    """
    Patch requests.post and requests.get so we don't make real HTTP calls
    to the FastAPI server. Instead, we'll return dummy data.
    """
    def fake_post(url, json, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "success"}
        return mock_response

    def fake_get(url, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # If the URL ends with /simulate_fast, return some sample metrics
        if "simulate_fast" in url:
            mock_response.json.return_value = {
                "avg_wait_time_n": 10,
                "avg_wait_time_s": 20,
                "avg_wait_time_e": 30,
                "avg_wait_time_w": 40,
                "max_wait_time_n": 50,
                "max_wait_time_s": 60,
                "max_wait_time_e": 70,
                "max_wait_time_w": 80,
                "max_queue_length_n": 5,
                "max_queue_length_s": 6,
                "max_queue_length_e": 7,
                "max_queue_length_w": 8,
            }
        else:
            mock_response.json.return_value = {"message": "success"}
        return mock_response

    monkeypatch.setattr("app.requests.post", fake_post)
    monkeypatch.setattr("app.requests.get", fake_get)

def test_dummy():
    """
    Just a sanity check to confirm pytest is running.
    """
    assert True

@patch("app.start_fastapi")
def test_start_simulation(mock_start_fastapi, client):
    response = client.post("/start_simulation")
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["message"] == "FastAPI server started"
    # Confirm that start_fastapi() was called
    mock_start_fastapi.assert_called_once()

@patch("app.stop_fastapi")
def test_stop_simulation(mock_stop_fastapi, client):
    response = client.post("/stop_simulation")
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["message"] == "FastAPI server stopped"
    # Confirm that stop_fastapi() was called
    mock_stop_fastapi.assert_called_once()

def test_start_session_api(client):
    response = client.post("/start_session")
    json_data = response.get_json()
    assert response.status_code == 200
    assert "session_id" in json_data
    assert json_data["message"] == "Session started"

def test_end_session_api(client):
    # First create a session in the database
    with app.app_context():
        session_id = create_session()
    # Then end it
    response = client.post("/end_session", json={"session_id": session_id})
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["message"] == "Session ended"
    # Verify session is inactive
    with app.app_context():
        from models import Session
        s = Session.query.get(session_id)
        assert s.active is False

def test_index_route(client):
    # The index route should render a template (status code 200).
    response = client.get("/")
    assert response.status_code == 200

def test_get_session_run_id(client):
    response = client.get("/get_session_run_id")
    json_data = response.get_json()
    assert response.status_code == 200
    assert "session_id" in json_data
    assert "run_id" in json_data

def test_parameters_get(client):
    response = client.get("/parameters")
    assert response.status_code == 200

def test_parameters_post(client):
    """
    Provide form data to /parameters and ensure it redirects upon success.
    """
    form_data = {
        "lanes": "4",
        "pedestrian-duration": "10",
        "pedestrian-frequency": "5",
        "nb_forward": "1",
        "nb_left": "2",
        "nb_right": "3",
        "sb_forward": "4",
        "sb_left": "5",
        "sb_right": "6",
        "eb_forward": "7",
        "eb_left": "8",
        "eb_right": "9",
        "wb_forward": "10",
        "wb_left": "11",
        "wb_right": "12",
        "left-turn": "on",
        "bus_lane": "on",
        "traffic-light-enable": "on",
        "tl_sequences": "5",
        "tl_vmain": "30",
        "tl_hmain": "40",
        "tl_vright": "20",
        "tl_hright": "25",
    }
    response = client.post("/parameters", data=form_data)
    # /parameters POST redirects to /junctionPage on success
    assert response.status_code in (302, 303)


def test_simulate(client):
    """
    /simulate is invoked with JSON including run_id, session_id
    and it returns 201 + some stats if successful.
    """
    payload = {"run_id": 1, "session_id": 1}
    response = client.post("/simulate", json=payload)
    assert response.status_code == 201
    json_data = response.get_json()
    assert "message" in json_data
    assert "score" in json_data

def test_junctionPage(client):
    response = client.get("/junctionPage")
    assert response.status_code == 200

def test_leaderboards(client):
    response = client.get("/leaderboards")
    assert response.status_code == 200

def test_session_leaderboard_page(client):
    response = client.get("/session_leaderboard?session_id=1")
    assert response.status_code == 200

def test_junction_details(client):
    with app.app_context():
        from models import db, Session, Configuration

        # 1. Create a session so session_id is valid
        session_obj = Session(active=True)
        db.session.add(session_obj)
        db.session.commit()

        # 2. Provide all required fields, including the total VPH columns
        config = Configuration(
            session_id=session_obj.id,
            run_id=999,
            pedestrian_duration=10,
            pedestrian_frequency=5,

            # North
            north_vph=1 + 2 + 3,  # sum of forward + left + right
            north_forward_vph=1,
            north_left_vph=2,
            north_right_vph=3,

            # South
            south_vph=4 + 5 + 6,
            south_forward_vph=4,
            south_left_vph=5,
            south_right_vph=6,

            # East
            east_vph=7 + 8 + 9,
            east_forward_vph=7,
            east_left_vph=8,
            east_right_vph=9,

            # West
            west_vph=10 + 11 + 12,
            west_forward_vph=10,
            west_left_vph=11,
            west_right_vph=12
        )
        db.session.add(config)
        db.session.commit()

    # Now call the endpoint
    response = client.get("/junction_details?run_id=999")
    assert response.status_code == 200

def test_process_csv_function():
    """
    Test the helper function process_csv in isolation.
    """
    from werkzeug.datastructures import FileStorage

    csv_content = (
        "pedestrian_duration,pedestrian_frequency,north_forward_vph,north_left_vph,north_right_vph,"
        "south_forward_vph,south_left_vph,south_right_vph,east_forward_vph,east_left_vph,east_right_vph,"
        "west_forward_vph,west_left_vph,west_right_vph\n"
        "10,5,1,2,3,4,5,6,7,8,9,10,11,12\n"
    )
    file = FileStorage(
        stream=BytesIO(csv_content.encode("utf-8")),
        filename="test.csv",
        content_type="text/csv",
    )
    configs = process_csv(file)
    assert len(configs) == 1
    assert configs[0].pedestrian_duration == "10"
    assert configs[0].pedestrian_frequency == "5"

def test_compute_score_4directions_function(client):
    """
    Test compute_score_4directions in isolation by adding a dummy LeaderboardResult
    so we have a global extreme to reference.
    """
    # Insert a single dummy result to define extremes
    dummy = LeaderboardResult(
        session_id=1,
        run_id=1,
        avg_wait_time_north=10,
        max_wait_time_north=50,
        max_queue_length_north=5,
        avg_wait_time_south=20,
        max_wait_time_south=60,
        max_queue_length_south=6,
        avg_wait_time_east=30,
        max_wait_time_east=70,
        max_queue_length_east=7,
        avg_wait_time_west=40,
        max_wait_time_west=80,
        max_queue_length_west=8
    )
    db.session.add(dummy)
    db.session.commit()

    score = compute_score_4directions(
        10, 50, 5,
        20, 60, 6,
        30, 70, 7,
        40, 80, 8
    )
    # Since the only record defines all extremes, the normalized score is 0
    assert score == 0

