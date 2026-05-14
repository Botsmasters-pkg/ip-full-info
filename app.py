from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import socket
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# =========================
# CONFIGURATION & CREDITS
# =========================
CREDIT_CHANNEL = "https://t.me/Toxicadminn"
CREDIT_SUPPORT = "https://t.me/botadminshere"
COPYRIGHT_NOTICE = f"👉 Channel: {CREDIT_CHANNEL} | Support: {CREDIT_SUPPORT}"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# =========================
# IP Info Service
# =========================
class IPInfoService:
    def __init__(self):
        self.services = [
            self._fetch_from_ipapi,
            self._fetch_from_ipinfo,
            self._fetch_from_ipgeolocation
        ]

    def _fetch_from_ipapi(self, ip_address: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f'http://ip-api.com/json/{ip_address}?fields=66846719', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'source': 'ip-api.com',
                        **data
                    }
        except Exception as e:
            logger.warning(f"ip-api.com failed: {str(e)}")
        return None

    def _fetch_from_ipinfo(self, ip_address: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                loc = data.get('loc', '').split(',')
                return {
                    'source': 'ipinfo.io',
                    'ip': ip_address,
                    'hostname': data.get('hostname'),
                    'city': data.get('city'),
                    'region': data.get('region'),
                    'country': data.get('country'),
                    'loc': data.get('loc'),
                    'lat': float(loc[0]) if loc and loc[0] else None,
                    'lon': float(loc[1]) if len(loc) > 1 else None,
                    'org': data.get('org'),
                    'postal': data.get('postal'),
                    'timezone': data.get('timezone'),
                }
        except Exception as e:
            logger.warning(f"ipinfo.io failed: {str(e)}")
        return None

    def _fetch_from_ipgeolocation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        try:
            API_KEY = ""  # Put your key here if you have
            if API_KEY:
                r = requests.get(f'https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={ip_address}', timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    data['source'] = 'ipgeolocation.io'
                    return data
        except Exception as e:
            logger.warning(f"ipgeolocation.io failed: {str(e)}")
        return None

    def _validate_ip(self, ip_address: str) -> bool:
        try:
            socket.inet_pton(socket.AF_INET, ip_address)
            return True
        except:
            try:
                socket.inet_pton(socket.AF_INET6, ip_address)
                return True
            except:
                return False

    def get_ip_info(self, ip_address: str) -> Dict[str, Any]:
        if not self._validate_ip(ip_address):
            return {'error': 'Invalid IP address format'}

        result = {
            'ip': ip_address,
            'timestamp': datetime.utcnow().isoformat(),
            'sources': [],
            'data': {},
            'credits': {
                'channel': CREDIT_CHANNEL,
                'support': CREDIT_SUPPORT,
                'notice': COPYRIGHT_NOTICE
            }
        }

        for service in self.services:
            data = service(ip_address)
            if data:
                source = data.pop('source')
                result['sources'].append(source)
                result['data'][source] = data

        if not result['sources']:
            result['error'] = 'Could not fetch IP information'

        return result


ip_service = IPInfoService()

# =========================
# ROUTES
# =========================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Pakistan IP Information API",
        "version": "1.2.0",
        "endpoints": {
            "/": "Home & Credits",
            "/api/v1/ip?ip=8.8.8.8": "Get IP Information",
            "/api/v1/myip": "Get Your IP Information",
            "/api/v1/bulk": "Bulk IP Lookup (POST)",
            "/api/v1/validate?ip=8.8.8.8": "Validate IP",
            "/api/v1/health": "Health Check",
            "/api/v1/stats": "API Stats"
        },
        "credits": {
            "channel": CREDIT_CHANNEL,
            "support": CREDIT_SUPPORT,
            "notice": COPYRIGHT_NOTICE
        }
    })


@app.route('/api/v1/ip', methods=['GET'])
def get_ip_info():
    ip_address = request.args.get('ip')
    if not ip_address:
        forwarded = request.headers.get('X-Forwarded-For')
        ip_address = forwarded.split(',')[0].strip() if forwarded else request.remote_addr

    data = ip_service.get_ip_info(ip_address)
    data['request'] = {
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    }
    return jsonify(data)


@app.route('/api/v1/myip', methods=['GET'])
def get_my_ip():
    forwarded = request.headers.get('X-Forwarded-For')
    client_ip = forwarded.split(',')[0].strip() if forwarded else request.remote_addr

    return jsonify({
        'your_ip': client_ip,
        'info': ip_service.get_ip_info(client_ip),
        'credits': COPYRIGHT_NOTICE
    })


@app.route('/api/v1/bulk', methods=['POST'])
def bulk_ip_lookup():
    try:
        data = request.get_json()
        if not data or 'ips' not in data:
            return jsonify({'error': 'Please send {"ips": ["1.1.1.1", "8.8.8.8"]}'}), 400

        ips = data['ips'][:10]  # max 10

        results = []
        for ip in ips:
            results.append({
                'ip': ip,
                'info': ip_service.get_ip_info(ip) if ip_service._validate_ip(ip) else {'error': 'Invalid IP'}
            })

        return jsonify({
            'count': len(results),
            'results': results,
            'credits': COPYRIGHT_NOTICE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/validate', methods=['GET'])
def validate_ip():
    ip = request.args.get('ip')
    if not ip:
        return jsonify({'error': 'IP parameter required'}), 400

    return jsonify({
        'ip': ip,
        'valid': ip_service._validate_ip(ip),
        'credits': COPYRIGHT_NOTICE
    })


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'IP Information API',
        'version': '1.2.0',
        'credits': COPYRIGHT_NOTICE
    })


@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'endpoints': 7,
        'services_used': ['ip-api.com', 'ipinfo.io'],
        'credits': COPYRIGHT_NOTICE
    })


# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found', 'credits': COPYRIGHT_NOTICE}), 404


if __name__ == '__main__':
    print("=" * 70)
    print("IP Information API Deployed Successfully!")
    print(f"Channel : {CREDIT_CHANNEL}")
    print(f"Support : {CREDIT_SUPPORT}")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)
