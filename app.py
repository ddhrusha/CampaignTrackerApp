from flask import Flask, jsonify, request, render_template
from uuid import uuid4
import json, threading, os
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
DB_FILE = 'campaigns.json'
lock = threading.Lock()

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump([], f)

def read_db():
    with lock:
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

def write_db(data):
    with lock:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    return jsonify(read_db())

@app.route('/api/campaigns', methods=['POST'])
def add_campaign():
    data = request.get_json()
    if not data or not all(k in data for k in ['campaign_name', 'client_name', 'start_date']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        datetime.strptime(data['start_date'], '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    new_campaign = {
        'id': str(uuid4()),
        'campaign_name': data['campaign_name'],
        'client_name': data['client_name'],
        'start_date': data['start_date'],
        'status': data.get('status', 'Active')
    }
    db = read_db()
    db.insert(0, new_campaign)
    write_db(db)
    return jsonify(new_campaign), 201

@app.route('/api/campaigns/<id>', methods=['PUT'])
def update_campaign(id):
    data = request.get_json()
    db = read_db()
    for c in db:
        if c['id'] == id:
            c.update({k: v for k, v in data.items() if k in ['campaign_name', 'client_name', 'start_date', 'status']})
            write_db(db)
            return jsonify(c)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/campaigns/<id>', methods=['DELETE'])
def delete_campaign(id):
    db = read_db()
    new_db = [c for c in db if c['id'] != id]
    if len(new_db) == len(db):
        return jsonify({'error': 'Not found'}), 404
    write_db(new_db)
    return jsonify({'message': 'Deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)
