from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)  # True when session is ongoing

    configurations = db.relationship('Configuration', backref='session', lazy=True)


class Configuration(db.Model):
    __tablename__ = 'configurations'
    run_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)  # Each configuration belongs to a session

    lanes = db.Column(db.Integer, nullable=False, default=5)  # Number of lanes
    left_turn_lane = db.Column(db.Boolean, nullable=False, default=False)  # Left-turn lane present
    bus_lane = db.Column(db.Boolean, default=False)  # Bus lane present

    pedestrian_duration = db.Column(db.Integer)  # Time for pedestrians to cross (s)
    pedestrian_frequency = db.Column(db.Integer)  # Crossing requests per hour

    # North
    north_vph = db.Column(db.Integer, nullable=False)
    north_forward_vph = db.Column(db.Integer, nullable=False)
    north_left_vph = db.Column(db.Integer, nullable=False)
    north_right_vph = db.Column(db.Integer, nullable=False)

    # South
    south_vph = db.Column(db.Integer, nullable=False)
    south_forward_vph = db.Column(db.Integer, nullable=False)
    south_left_vph = db.Column(db.Integer, nullable=False)
    south_right_vph = db.Column(db.Integer, nullable=False)

    # East
    east_vph = db.Column(db.Integer, nullable=False)
    east_forward_vph = db.Column(db.Integer, nullable=False)
    east_left_vph = db.Column(db.Integer, nullable=False)
    east_right_vph = db.Column(db.Integer, nullable=False)

    # West
    west_vph = db.Column(db.Integer, nullable=False)
    west_forward_vph = db.Column(db.Integer, nullable=False)
    west_left_vph = db.Column(db.Integer, nullable=False)
    west_right_vph = db.Column(db.Integer, nullable=False)


class LeaderboardResult(db.Model):
    __tablename__ = 'leaderboard_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    # North direction metrics
    avg_wait_time_north = db.Column(db.Float, nullable=False)
    max_wait_time_north = db.Column(db.Float, nullable=False)
    max_queue_length_north = db.Column(db.Integer, nullable=False)

    # South direction metrics
    avg_wait_time_south = db.Column(db.Float, nullable=False)
    max_wait_time_south = db.Column(db.Float, nullable=False)
    max_queue_length_south = db.Column(db.Integer, nullable=False)

    # East direction metrics
    avg_wait_time_east = db.Column(db.Float, nullable=False)
    max_wait_time_east = db.Column(db.Float, nullable=False)
    max_queue_length_east = db.Column(db.Integer, nullable=False)

    # West direction metrics
    avg_wait_time_west = db.Column(db.Float, nullable=False)
    max_wait_time_west = db.Column(db.Float, nullable=False)
    max_queue_length_west = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "avg_wait_time_north": self.avg_wait_time_north,
            "max_wait_time_north": self.max_wait_time_north,
            "max_queue_length_north": self.max_queue_length_north,
            "avg_wait_time_south": self.avg_wait_time_south,
            "max_wait_time_south": self.max_wait_time_south,
            "max_queue_length_south": self.max_queue_length_south,
            "avg_wait_time_east": self.avg_wait_time_east,
            "max_wait_time_east": self.max_wait_time_east,
            "max_queue_length_east": self.max_queue_length_east,
            "avg_wait_time_west": self.avg_wait_time_west,
            "max_wait_time_west": self.max_wait_time_west,
            "max_queue_length_west": self.max_queue_length_west
        }


class TrafficSettings(db.Model):
    __tablename__ = 'traffic_settings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    enabled = db.Column(db.Boolean, nullable=False, default=False)
    sequences_per_hour = db.Column(db.Integer, nullable=False, default=0)
    vertical_main_green = db.Column(db.Integer, nullable=False, default=0)
    horizontal_main_green = db.Column(db.Integer, nullable=False, default=0)
    vertical_right_green = db.Column(db.Integer, nullable=False, default=0)
    horizontal_right_green = db.Column(db.Integer, nullable=False, default=0)

    const_gaps_in_sequence = db.Column(db.Integer, default=5 * 1)

    def serialize(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "enabled": self.enabled,
            "sequences_per_hour": self.sequences_per_hour,
            "vertical_main_green": self.vertical_main_green,
            "horizontal_main_green": self.horizontal_main_green,
            "vertical_right_green": self.vertical_right_green,
            "horizontal_right_green": self.horizontal_right_green
        }
