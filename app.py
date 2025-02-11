from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
#import os

from db_schema import db

app = Flask(__name__)

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# reset database (if needed)
resetdb = False
if resetdb:
    with app.app_context():
        db.drop_all()
        db.create_all()

# direct dashboard route
@app.route('/')
def index():
    return redirect('/dashboard')

@app.route('/home')
def home():
    return redirect('/dashboard')

# dashboard route
@app.route('/dashboard')
def dash():
    return render_template('dashboard.html')

# reset database route (if needed)
@app.route('/resetdb')
def reset_db():
    db.drop_all()
    db.create_all()
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
