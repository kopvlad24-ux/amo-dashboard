from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='static')
CORS(app)

SUBDOMAIN = 'c21pp'
BASE = f'https://{SUBDOMAIN}.amocrm.ru'
CLUB_GROUP_ID = 689470
EXCLUDED_USER_IDS = {13290234, 13324978}

CLIENT_ID     = os.environ.get('AMO_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AMO_CLIENT_SECRET', '')

# Храним актуальный токен в памяти (обновляется через refresh)
_current_token = {'value': os.environ.get('AMO_ACCESS_TOKEN', '')}
_refresh_token  = {'value': os.environ.get('AMO_REFRESH_TOKEN', '')}

@app.route('/api/token')
def get_token():
    return jsonify({'token': _current_token['value']})

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/proxy/<path:path>')
def proxy(path):
    token = _current_token['value']
    if not token:
        return jsonify({'error': 'No token configured'}), 401
    params = dict(request.args)
    try:
        r = requests.get(
            f'{BASE}/api/v4/{path}',
            headers={'Authorization': f'Bearer {token}'},
            params=params,
            timeout=15
        )
        # Если токен истёк — пробуем refresh
        if r.status_code == 401 and _refresh_token['value'] and CLIENT_ID and CLIENT_SECRET:
            refreshed = _do_refresh()
            if refreshed:
                r = requests.get(
                    f'{BASE}/api/v4/{path}',
                    headers={'Authorization': f'Bearer {_current_token["value"]}'},
                    params=params,
                    timeout=15
                )
        return (r.content, r.status_code, {'Content-Type': 'application/json'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _do_refresh():
    try:
        r = requests.post(f'{BASE}/oauth2/access_token', json={
            'client_id':     CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type':    'refresh_token',
            'refresh_token': _refresh_token['value'],
            'redirect_uri':  'https://localhost'
        }, timeout=15)
        if r.ok:
            data = r.json()
            _current_token['value'] = data.get('access_token', _current_token['value'])
            _refresh_token['value'] = data.get('refresh_token', _refresh_token['value'])
            return True
    except:
        pass
    return False

@app.route('/api/group_users')
def group_users():
    token = _current_token['value']
    if not token:
        return jsonify({'error': 'No token configured'}), 401
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
    if not CLIENT_ID or not CLIENT_SECRET:
        return jsonify({'error': 'CLIENT_ID/CLIENT_SECRET не заданы на сервере'}), 500
    try:
        r = requests.post(f'{BASE}/oauth2/access_token', json={
            'client_id':     CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type':    'refresh_token',
            'refresh_token': data.get('refresh_token', ''),
            'redirect_uri':  'https://localhost'
        }, timeout=15)
        return (r.content, r.status_code, {'Content-Type': 'application/json'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    app.run(host='0.0.0.0', port=port)
