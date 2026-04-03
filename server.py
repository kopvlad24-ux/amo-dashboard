from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='static')
CORS(app)

SUBDOMAIN = 'c21pp'
BASE = f'https://{SUBDOMAIN}.amocrm.ru'
CLUB_GROUP_ID = 689470  # Клуб чемпионов
EXCLUDED_USER_IDS = {13290234, 13324978}  # Валиева Валерия, Фатхуллов Рустем

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/proxy/<path:path>')
def proxy(path):
    token = request.headers.get('X-Token')
    if not token:
        return jsonify({'error': 'No token'}), 401
    params = dict(request.args)
    try:
        r = requests.get(
            f'{BASE}/api/v4/{path}',
            headers={'Authorization': f'Bearer {token}'},
            params=params,
            timeout=15
        )
        return (r.content, r.status_code, {'Content-Type': 'application/json'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/group_users')
def group_users():
    token = request.headers.get('X-Token')
    if not token:
        return jsonify({'error': 'No token'}), 401
    try:
        r = requests.get(
            f'{BASE}/api/v4/users',
            headers={'Authorization': f'Bearer {token}'},
            params={'limit': 250, 'with': 'group'},
            timeout=15
        )
        users_data = r.json()
        users = users_data.get('_embedded', {}).get('users', [])

        filtered = [
            u for u in users
            if u.get('rights', {}).get('group_id') == CLUB_GROUP_ID
            and u.get('rights', {}).get('is_active', False)
            and u.get('id') not in EXCLUDED_USER_IDS
        ]

        return jsonify({
            'users': filtered,
            'group_found': True,
            'group_name': 'Клуб чемпионов',
            'count': len(filtered)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_token():
    data = request.json
    try:
        r = requests.post(f'{BASE}/oauth2/access_token', json={
            'client_id': data['client_id'],
            'client_secret': data['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': data['refresh_token'],
            'redirect_uri': 'https://localhost'
        }, timeout=15)
        return (r.content, r.status_code, {'Content-Type': 'application/json'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    app.run(host='0.0.0.0', port=port)
