from flask import Flask, jsonify, request, send_from_directory, Response
from dotenv import load_dotenv
import hmac
import requests
import os

load_dotenv()

app = Flask(__name__, static_folder='static')

SUBDOMAIN = os.environ.get('AMO_SUBDOMAIN', 'c21pp')
BASE = f'https://{SUBDOMAIN}.amocrm.ru'
CLUB_GROUP_ID = 689470
EXCLUDED_USER_IDS = {13290234, 13324978}

CLIENT_ID     = os.environ.get('AMO_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AMO_CLIENT_SECRET', '')
DASHBOARD_USER = os.environ.get('DASHBOARD_USER', '')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', '')

# AMO_TOKEN поддерживает долгосрочный токен, уже используемый в других сервисах.
# AMO_ACCESS_TOKEN оставлен для OAuth-интеграций.
_current_token = {'value': os.environ.get('AMO_ACCESS_TOKEN') or os.environ.get('AMO_TOKEN', '')}
_refresh_token  = {'value': os.environ.get('AMO_REFRESH_TOKEN', '')}

ALLOWED_PROXY_PATHS = {'users', 'leads', 'leads/pipelines', 'tasks'}

@app.before_request
def require_dashboard_auth():
    if request.path == '/api/health':
        return None
    if not DASHBOARD_USER or not DASHBOARD_PASSWORD:
        return jsonify({'error': 'Dashboard credentials are not configured'}), 503
    auth = request.authorization
    valid = (
        auth
        and hmac.compare_digest(auth.username or '', DASHBOARD_USER)
        and hmac.compare_digest(auth.password or '', DASHBOARD_PASSWORD)
    )
    if not valid:
        return Response(
            'Authentication required',
            401,
            {'WWW-Authenticate': 'Basic realm="AMO Dashboard"'}
        )
    return None

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'amo_configured': bool(_current_token['value']),
        'dashboard_auth_configured': bool(DASHBOARD_USER and DASHBOARD_PASSWORD),
        'amo_domain': f'{SUBDOMAIN}.amocrm.ru'
    })

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/proxy/<path:path>')
def proxy(path):
    if path not in ALLOWED_PROXY_PATHS:
        return jsonify({'error': 'AMO resource is not allowed'}), 403
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    app.run(host='0.0.0.0', port=port)
