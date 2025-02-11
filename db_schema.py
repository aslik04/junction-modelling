from flask_sqlalchemy import SQLAlchemy
#from flask_login import UserMixin

#from werkzeug import security
#import datetime
#from sqlalchemy.inspection import inspect

#from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# create the database schema
db = SQLAlchemy()

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Configuration(db.Model):
    __tablename__ = 'configuration'
    
    runid = db.Column(db.Integer, primary_key=True, autoincrement=True)

    N_LeftLane = db.Column(db.Integer, nullable=False)  # should be either 0 or 1
    N_NoOfLanes = db.Column(db.Integer, nullable=False)  # should be from 1 to 5
    N_Pedestrians = db.Column(db.Integer, nullable=False)  # should be either 0 or 1

    E_LeftLane = db.Column(db.Integer, nullable=False)  
    E_NoOfLanes = db.Column(db.Integer, nullable=False)  
    E_Pedestrians = db.Column(db.Integer, nullable=False)  

    S_LeftLane = db.Column(db.Integer, nullable=False)  
    S_NoOfLanes = db.Column(db.Integer, nullable=False)  
    S_Pedestrians = db.Column(db.Integer, nullable=False)  

    W_LeftLane = db.Column(db.Integer, nullable=False)  
    W_NoOfLanes = db.Column(db.Integer, nullable=False)  
    W_Pedestrians = db.Column(db.Integer, nullable=False)  

    def __init__(self, N_LeftLane, N_NoOfLanes, N_Pedestrians, 
                 E_LeftLane, E_NoOfLanes, E_Pedestrians, 
                 S_LeftLane, S_NoOfLanes, S_Pedestrians, 
                 W_LeftLane, W_NoOfLanes, W_Pedestrians):
        
        self.N_LeftLane = N_LeftLane
        self.N_NoOfLanes = N_NoOfLanes
        self.N_Pedestrians = N_Pedestrians

        self.E_LeftLane = E_LeftLane
        self.E_NoOfLanes = E_NoOfLanes
        self.E_Pedestrians = E_Pedestrians

        self.S_LeftLane = S_LeftLane
        self.S_NoOfLanes = S_NoOfLanes
        self.S_Pedestrians = S_Pedestrians

        self.W_LeftLane = W_LeftLane
        self.W_NoOfLanes = W_NoOfLanes
        self.W_Pedestrians = W_Pedestrians


class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    
    runid = db.Column(db.Integer, db.ForeignKey("configuration.runid"), primary_key=True, autoincrement=True)
    
    N_AvWaitTime = db.Column(db.Float(2))
    N_MaxWaitTime = db.Column(db.Float(2))
    N_MaxQueueLen = db.Column(db.Integer)

    E_AvWaitTime = db.Column(db.Float(2))
    E_MaxWaitTime = db.Column(db.Float(2))
    E_MaxQueueLen = db.Column(db.Integer)

    S_AvWaitTime = db.Column(db.Float(2))
    S_MaxWaitTime = db.Column(db.Float(2))
    S_MaxQueueLen = db.Column(db.Integer)

    W_AvWaitTime = db.Column(db.Float(2))
    W_MaxWaitTime = db.Column(db.Float(2))
    W_MaxQueueLen = db.Column(db.Integer)

    Score = db.Column(db.Float(2))

    def __init__(self, N_AvWaitTime, N_MaxWaitTime, N_MaxQueueLen, 
                 E_AvWaitTime, E_MaxWaitTime, E_MaxQueueLen, 
                 S_AvWaitTime, S_MaxWaitTime, S_MaxQueueLen, 
                 W_AvWaitTime, W_MaxWaitTime, W_MaxQueueLen, Score):
        
        self.N_AvWaitTime = N_AvWaitTime
        self.N_MaxWaitTime = N_MaxWaitTime
        self.N_MaxQueueLen = N_MaxQueueLen

        self.E_AvWaitTime = E_AvWaitTime
        self.E_MaxWaitTime = E_MaxWaitTime
        self.E_MaxQueueLen = E_MaxQueueLen

        self.S_AvWaitTime = S_AvWaitTime
        self.S_MaxWaitTime = S_MaxWaitTime
        self.S_MaxQueueLen = S_MaxQueueLen

        self.W_AvWaitTime = W_AvWaitTime
        self.W_MaxWaitTime = W_MaxWaitTime
        self.W_MaxQueueLen = W_MaxQueueLen

        self.Score = Score

def dbinit():
    db.create_all()
