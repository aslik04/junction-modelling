from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Attempts(db.Model):
    __tablename__ = 'attempts'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("configurations.run_id"))

    N_LeftLane = db.Column(db.Integer, nullable=False)  # should be either 0 or 1
    N_NoOfLanes = db.Column(db.Integer, nullable=False)  # should be from 1 to 5

    E_LeftLane = db.Column(db.Integer, nullable=False)  
    E_NoOfLanes = db.Column(db.Integer, nullable=False)  

    S_LeftLane = db.Column(db.Integer, nullable=False)  
    S_NoOfLanes = db.Column(db.Integer, nullable=False)  

    W_LeftLane = db.Column(db.Integer, nullable=False)  
    W_NoOfLanes = db.Column(db.Integer, nullable=False)  

    # Relationship: One Attempt -> One LeaderboardResult (probably optional)
    leaderboard_result = db.relationship('LeaderboardResult', backref='attempts', uselist=False)


class Configuration(db.Model):
    __tablename__ = 'configurations'
    run_id = db.Column(db.Integer, primary_key=True)
    #lanes = db.Column(db.Integer, nullable=False)  Don't need this since it is in Attempts
    pedestrian_crossings = db.Column(db.Boolean, nullable=False)
    pedestrian_time = db.Column(db.Integer) #Time for pedestrains to cross (s)
    pedestrian_frequency = db.column(db.Integer) #Crossing requests per hour
    #TODO: Do we also need time to run for?

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



class LeaderboardResult(db.Model):
    __tablename__ = 'leaderboard_results'
    id = db.Column(db.Integer, db.ForeignKey('attempts.id'), primary_key=True)  # FK constraint
    run_id = db.Column(db.Integer, db.ForeignKey('configurations.run_id'), nullable=False)
    avg_wait_time = db.Column(db.Float, nullable=False)
    max_wait_time = db.Column(db.Float, nullable=False)
    max_queue_length = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
