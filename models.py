"""
This file defines the database models for a traffic junction simulation system using SQLAlchemy.
It includes models for managing sessions, configurations, traffic results, and Algoirthm data.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialise SQLAlchemy database instance
db = SQLAlchemy()

class Session(db.Model):
    """
    Represents a simulation session that can contain multiple configurations.
    Tracks the creation time and active status of simulation sessions.
    Created When user presses begin on index page.
    """
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)  # True when session is ongoing

    configurations = db.relationship('Configuration', backref='session', lazy=True)


class Configuration(db.Model):
    """
    Stores the configuration parameters for each traffic simulation run.
    Includes lane setup, traffic volumes, and directional flow settings.
    All configuration data from a user, except the users traffic settings.
    """
    __tablename__ = 'configurations'
    run_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    # Lane configuration
    lanes = db.Column(db.Integer, nullable=False, default=5)
    left_turn_lane = db.Column(db.Boolean, nullable=False, default=False)
    bus_lane = db.Column(db.Boolean, default=False)

    # Pedestrian settings
    pedestrian_duration = db.Column(db.Integer)  # Time for pedestrians to cross (s)
    pedestrian_frequency = db.Column(db.Integer)  # Crossing requests per hour

    # Traffic volume settings for each direction (North)
    north_vph = db.Column(db.Integer, nullable=False)
    north_forward_vph = db.Column(db.Integer, nullable=False)
    north_left_vph = db.Column(db.Integer, nullable=False)
    north_right_vph = db.Column(db.Integer, nullable=False)

    # Traffic volume settings for each direction (South)
    south_vph = db.Column(db.Integer, nullable=False)
    south_forward_vph = db.Column(db.Integer, nullable=False)
    south_left_vph = db.Column(db.Integer, nullable=False)
    south_right_vph = db.Column(db.Integer, nullable=False)

    # Traffic volume settings for each direction (East)
    east_vph = db.Column(db.Integer, nullable=False)
    east_forward_vph = db.Column(db.Integer, nullable=False)
    east_left_vph = db.Column(db.Integer, nullable=False)
    east_right_vph = db.Column(db.Integer, nullable=False)

    # Traffic volume settings for each direction (West)
    west_vph = db.Column(db.Integer, nullable=False)
    west_forward_vph = db.Column(db.Integer, nullable=False)
    west_left_vph = db.Column(db.Integer, nullable=False)
    west_right_vph = db.Column(db.Integer, nullable=False)


class LeaderboardResult(db.Model):
    """
    Stores simulation results for the leaderboard.
    Tracks metrics like wait times and queue lengths for each direction.
    This data is for users results, which will be compared against
    dynamic algorithms score metrics.
    """
    __tablename__ = 'leaderboard_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    # Performance metrics for North direction
    avg_wait_time_north = db.Column(db.Float, nullable=False)
    max_wait_time_north = db.Column(db.Float, nullable=False)
    max_queue_length_north = db.Column(db.Integer, nullable=False)

    # Performance metrics for South direction
    avg_wait_time_south = db.Column(db.Float, nullable=False)
    max_wait_time_south = db.Column(db.Float, nullable=False)
    max_queue_length_south = db.Column(db.Integer, nullable=False)

    # Performance metrics for East direction
    avg_wait_time_east = db.Column(db.Float, nullable=False)
    max_wait_time_east = db.Column(db.Float, nullable=False)
    max_queue_length_east = db.Column(db.Integer, nullable=False)

    # Performance metrics for West direction
    avg_wait_time_west = db.Column(db.Float, nullable=False)
    max_wait_time_west = db.Column(db.Float, nullable=False)
    max_queue_length_west = db.Column(db.Integer, nullable=False)

    def serialize(self):
        """Converts the model instance to a dictionary for JSON serialisation"""
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
    """
    Stores traffic light timing and sequence settings for each simulation run.
    Controls the traffic light behavior and timing patterns.
    These configurations are chosen by user, either enabled or disabled,
    enabled lets user view their own traffic light logic,
    disabled they can view our highly efficient dynamic algorithm.
    """
    __tablename__ = 'traffic_settings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    # Traffic light control settings
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    sequences_per_hour = db.Column(db.Integer, nullable=False, default=0)
    vertical_main_green = db.Column(db.Integer, nullable=False, default=0)
    horizontal_main_green = db.Column(db.Integer, nullable=False, default=0)
    vertical_right_green = db.Column(db.Integer, nullable=False, default=0)
    horizontal_right_green = db.Column(db.Integer, nullable=False, default=0)

    const_gaps_in_sequence = db.Column(db.Integer, default=5)

    def serialize(self):
        """Converts the model instance to a dictionary for JSON serialisation"""
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


class AlgorithmLeaderboardResult(db.Model):
    """
    Stores algorithm-specific simulation results for the leaderboard.
    Similar to LeaderboardResult but specifically for algorithm performance tracking.
    Stores runs where user both enabled or disabled user traffic settings contrary to other leaderboard.
    """
    __tablename__ = 'algorithm_leaderboard_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    # Performance metrics for North direction
    avg_wait_time_north = db.Column(db.Float, nullable=False)
    max_wait_time_north = db.Column(db.Float, nullable=False)
    max_queue_length_north = db.Column(db.Integer, nullable=False)

    # Performance metrics for South direction
    avg_wait_time_south = db.Column(db.Float, nullable=False)
    max_wait_time_south = db.Column(db.Float, nullable=False)
    max_queue_length_south = db.Column(db.Integer, nullable=False)

    # Performance metrics for East direction
    avg_wait_time_east = db.Column(db.Float, nullable=False)
    max_wait_time_east = db.Column(db.Float, nullable=False)
    max_queue_length_east = db.Column(db.Integer, nullable=False)

    # Performance metrics for West direction
    avg_wait_time_west = db.Column(db.Float, nullable=False)
    max_wait_time_west = db.Column(db.Float, nullable=False)
    max_queue_length_west = db.Column(db.Integer, nullable=False)

    def serialize(self):
        """Converts the model instance to a dictionary for JSON serialisation"""
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