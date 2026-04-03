from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='static')
CORS(app)

SUBDOMAIN = 'c21pp'
BASE = f'https://{SUBDOMAIN}.amocrm.ru'

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
    group_name = request.args.get('name', 'Клуб чемпионов')
    if not token:
        return jsonify({'error': 'No token'}), 401
    try:
        # Try groups endpoint
        r = requests.get(f'{BASE}/api/v4/users/groups', headers={'Authorization': f'Bearer {token}'}, params={'limit': 250}, timeout=15)
        groups_data = r.json()
        groups = groups_data.get('_embedded', {}).get('groups', [])

        target_group = next((g for g in groups if g.get('name') == group_name), None)

        # Get all users
        users_r = requests.get(f'{BASE}/api/v4/users', headers={'Authorization': f'Bearer {token}'}, params={'limit': 250, 'with': 'group'}, timeout=15)
        users_data = users_r.json()
        users = users_data.get('_embedded', {}).get('users', [])

        if target_group:
            group_id = target_group['id']
            filtered = [u for u in users if u.get('group_id') == group_id or
                        any(g.get('id') == group_id for g in (u.get('_embedded', {}).get('groups', [])))]
        else:
            filtered = users

        return jsonify({
            'users': filtered,
            'group_found': target_group is not None,
            'group_name': group_name,
            'all_groups': [{'id': g['id'], 'name': g['name']} for g in groups],
            'debug_users_sample': [{'id': u['id'], 'name': u['name'], 'group_id': u.get('group_id'), 'embedded': u.get('_embedded', {})} for u in users[:3]]
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
