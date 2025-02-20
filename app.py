from flask import Flask, request, jsonify, render_template
from models import db, Configuration, LeaderboardResult, Session
from sqlalchemy import inspect
import csv
import io
import random
import os

app = Flask(__name__)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'traffic_junction.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize database, needed os.path to to not create db in instance folder
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("Tables created:", inspector.get_table_names())
    print("Database path:", os.path.abspath('traffic_junction.db'))


def create_session():
    session = Session()
    db.session.add(session)
    db.session.commit()
    return session.id

def end_session(session_id):
    session = Session.query.get(session_id)
    if session:
        session.active = False
        db.session.commit()



def get_session_leaderboard(session_id):
    """Gets the top 10 scores for a specific session."""
    return LeaderboardResult.query.filter_by(session_id=session_id).order_by(LeaderboardResult.score.desc()).limit(10).all()


def get_all_time_leaderboard():
    """Gets the top 10 scores across all sessions."""
    return LeaderboardResult.query.order_by(LeaderboardResult.score.desc()).limit(10).all()


def save_session_leaderboard_result(session_id, run_id, avg_wait_time, max_wait_time, max_queue_length, score):
    """Saves a session leaderboard result without deleting older results."""

    result = LeaderboardResult(
        session_id=session_id,
        run_id=run_id,
        avg_wait_time=avg_wait_time,
        max_wait_time=max_wait_time,
        max_queue_length=max_queue_length,
        score=score
    )
    db.session.add(result)
    db.session.commit()





# To Process CSV data instead of input text boxes
def process_csv(file):
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)
    configurations = []
    for row in csv_input:
        config = Configuration(
            run_id=row['run_id'],
            #lanes=row['lanes'],
            pedestrian_crossings = str(row['pedestrian_crossings']).strip().lower() == 'true',
            pedestrian_time=row['pedestrian_time'],
            pedestrian_frequency=row['pedestrian_frequency'],

            north_vph=row['north_vph'],
            north_exit_east_vph=row['north_exit_east_vph'],
            north_exit_west_vph=row['north_exit_west_vph'],
            north_exit_south_vph=row['north_exit_south_vph'],

            south_vph=row['south_vph'],
            south_exit_east_vph=row['south_exit_east_vph'],
            south_exit_west_vph=row['south_exit_west_vph'],
            south_exit_north_vph=row['south_exit_north_vph'],

            east_vph=row['east_vph'],
            east_exit_north_vph=row['east_exit_north_vph'],
            east_exit_south_vph=row['east_exit_south_vph'],
            east_exit_west_vph=row['east_exit_west_vph'],

            west_vph=row['west_vph'],
            west_exit_north_vph=row['west_exit_north_vph'],
            west_exit_south_vph=row['west_exit_south_vph'],
            west_exit_east_vph=row['west_exit_east_vph']
        )
        configurations.append(config)
    return configurations

@app.route('/start_session', methods=['POST'])
def start_session_api():
    session_id = create_session() 
    return jsonify({"session_id": session_id, "message": "Session started"})

@app.route('/end_session', methods=['POST'])
def end_session_api():
    session_id = request.json.get('session_id')
    end_session(session_id) 
    return jsonify({'message': 'Session ended'})


@app.route('/')
def index():
    session_id = create_session()
    return render_template('index.html', session_id=session_id)

@app.route('/parameters')
def parameters():
    # Renders the template below (in the 'templates' folder as 'index.html')
    return render_template('parameters.html')

@app.route('/upload-file', methods=['POST'])
def uploadfile():
    if 'file' not in request.files:
        return "No file part in the request.", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected.", 400

    # Do something with the uploaded file here, e.g. save it:
    # file.save("some/path/" + file.filename)

    return f"File '{file.filename}' uploaded successfully!"



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            if 'file' in request.files:
                file = request.files['file']
                configurations = process_csv(file)
                for config in configurations:
                    db.session.add(config)
                db.session.commit()
                return render_template('success.html', message='parameters saved')
            else:
                data = request.form
                config = Configuration(
                    run_id=data.get('run_id'),
                    #lanes=data.get('lanes'),
                    pedestrian_crossings='pedestrian_crossings' in data,
                    pedestrian_time=data.get('pedestrian_time'),
                    pedestrian_frequency=data.get('pedestrian_frequency'),

                    north_vph=data.get('north_vph'),
                    north_exit_east_vph=data.get('north_exit_east_vph'),
                    north_exit_west_vph=data.get('north_exit_west_vph'),
                    north_exit_south_vph=data.get('north_exit_south_vph'),

                    south_vph=data.get('south_vph'),
                    south_exit_east_vph=data.get('south_exit_east_vph'),
                    south_exit_west_vph=data.get('south_exit_west_vph'),
                    south_exit_north_vph=data.get('south_exit_north_vph'),

                    east_vph=data.get('east_vph'),
                    east_exit_north_vph=data.get('east_exit_north_vph'),
                    east_exit_south_vph=data.get('east_exit_south_vph'),
                    east_exit_west_vph=data.get('east_exit_west_vph'),

                    west_vph=data.get('west_vph'),
                    west_exit_north_vph=data.get('west_exit_north_vph'),
                    west_exit_south_vph=data.get('west_exit_south_vph'),
                    west_exit_east_vph=data.get('west_exit_east_vph')
                )
                db.session.add(config)
                db.session.commit()
                return render_template('success.html')
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    return render_template('upload.html')


@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        run_id = data.get('run_id')
        session_id = data.get('session_id')

        avg_wait_time = random.uniform(5, 20)
        max_wait_time = random.uniform(avg_wait_time, 40)
        max_queue_length = random.randint(10, 50)
        score = avg_wait_time + (max_wait_time / 2) + (max_queue_length / 5)

        save_session_leaderboard_result(session_id, run_id, avg_wait_time, max_wait_time, max_queue_length, score)

        return jsonify({
            'message': 'sim results saved',
            'avg_wait_time': avg_wait_time,
            'max_wait_time': max_wait_time,
            'max_queue_length': max_queue_length,
            'score': score
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400



@app.route('/leaderboards')
def leaderboards():
    top_results = get_all_time_leaderboard() 
    return render_template('leaderboards.html', results=top_results)



@app.route('/leaderboard/session/<int:session_id>', methods=['GET'])
def session_leaderboard(session_id):
    results = get_session_leaderboard(session_id)
    if not results:
        return jsonify({"message": "no results for this session"}), 200
    return jsonify([r.serialize() for r in results])


@app.route('/leaderboard/all_time', methods=['GET'])
def all_time_leaderboard():
    results = get_all_time_leaderboard()
    if not results:
        return jsonify({"message": "no results found"}), 200
    return jsonify([r.serialize() for r in results])



if __name__ == '__main__':
    app.run(debug=True)
