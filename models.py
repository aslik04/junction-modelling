from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Configuration(db.Model):
    __tablename__ = 'configurations'
    run_id = db.Column(db.Integer, primary_key=True)
    lanes = db.Column(db.Integer, nullable=False)
    pedestrian_crossings = db.Column(db.Boolean, nullable=False)

    north_vph = db.Column(db.Integer, nullable=False)
    north_exit_east_vph = db.Column(db.Integer, nullable=False)
    north_exit_west_vph = db.Column(db.Integer, nullable=False)
    north_exit_south_vph = db.Column(db.Integer, nullable=False)

    south_vph = db.Column(db.Integer, nullable=False)
    south_exit_east_vph = db.Column(db.Integer, nullable=False)
    south_exit_west_vph = db.Column(db.Integer, nullable=False)
    south_exit_north_vph = db.Column(db.Integer, nullable=False)

    east_vph = db.Column(db.Integer, nullable=False)
    east_exit_north_vph = db.Column(db.Integer, nullable=False)
    east_exit_south_vph = db.Column(db.Integer, nullable=False)
    east_exit_west_vph = db.Column(db.Integer, nullable=False)

    west_vph = db.Column(db.Integer, nullable=False)
    west_exit_north_vph = db.Column(db.Integer, nullable=False)
    west_exit_south_vph = db.Column(db.Integer, nullable=False)
    west_exit_east_vph = db.Column(db.Integer, nullable=False)

    #Relation between tables
    leaderboard_result = db.relationship('LeaderboardResult', backref='configuration', uselist=False)

class LeaderboardResult(db.Model):
    __tablename__ = 'leaderboard_results'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    avg_wait_time = db.Column(db.Float, nullable=False)
    max_wait_time = db.Column(db.Float, nullable=False)
    max_queue_length = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
