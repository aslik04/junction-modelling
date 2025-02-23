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

    lanes = db.Column(db.Integer, nullable=False, default=2)  # Number of lanes
    left_turn_lane = db.Column(db.Boolean, nullable=False, default=False)  # Left-turn lane present

    pedestrian_crossings = db.Column(db.Integer, nullable=False, default=0)  
    pedestrian_time = db.Column(db.Integer)  # Time for pedestrians to cross (s)
    pedestrian_frequency = db.Column(db.Integer)  # Crossing requests per hour

    # Northbound
    north_vph = db.Column(db.Integer, nullable=False)
    north_exit_east_vph = db.Column(db.Integer, nullable=False)
    north_exit_west_vph = db.Column(db.Integer, nullable=False)
    north_exit_south_vph = db.Column(db.Integer, nullable=False)

    # Southbound
    south_vph = db.Column(db.Integer, nullable=False)
    south_exit_east_vph = db.Column(db.Integer, nullable=False)
    south_exit_west_vph = db.Column(db.Integer, nullable=False)
    south_exit_north_vph = db.Column(db.Integer, nullable=False)

    # Eastbound
    east_vph = db.Column(db.Integer, nullable=False)
    east_exit_north_vph = db.Column(db.Integer, nullable=False)
    east_exit_south_vph = db.Column(db.Integer, nullable=False)
    east_exit_west_vph = db.Column(db.Integer, nullable=False)

    # Westbound
    west_vph = db.Column(db.Integer, nullable=False)
    west_exit_north_vph = db.Column(db.Integer, nullable=False)
    west_exit_south_vph = db.Column(db.Integer, nullable=False)
    west_exit_east_vph = db.Column(db.Integer, nullable=False)


class LeaderboardResult(db.Model):
    __tablename__ = 'leaderboard_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)  # Always store session ID

    avg_wait_time = db.Column(db.Float, nullable=False)
    max_wait_time = db.Column(db.Float, nullable=False)
    max_queue_length = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "avg_wait_time": self.avg_wait_time,
            "max_wait_time": self.max_wait_time,
            "max_queue_length": self.max_queue_length,
            "score": self.score
        }
