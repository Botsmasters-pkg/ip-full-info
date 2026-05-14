
# app.py - Main Flask Application
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import socket
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class IPInfoService:
    """Service class for fetching IP information from various APIs"""
    
    def __init__(self):
        self.services = [
            self._fetch_from_ipapi,
            self._fetch_from_ipinfo,
            self._fetch_from_ipgeolocation
        ]
    
    def _fetch_from_ipapi(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Fetch data from ip-api.com"""
        try:
            response = requests.get(f'http://ip-api.com/json/{ip_address}?fields=66846719', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'source': 'ip-api.com',
                        'ip': ip_address,
                        'continent': data.get('continent', ''),
                        'continent_code': data.get('continentCode', ''),
                        'country': data.get('country', ''),
                        'country_code': data.get('countryCode', ''),
                        'region': data.get('regionName', ''),
                        'region_code': data.get('region', ''),
                        'city': data.get('city', ''),
                        'district': data.get('district', ''),
                        'zip': data.get('zip', ''),
                        'lat': data.get('lat', 0),
                        'lon': data.get('lon', 0),
                        'timezone': data.get('timezone', ''),
                        'offset': data.get('offset', 0),
                        'currency': data.get('currency', ''),
                        'isp': data.get('isp', ''),
                        'org': data.get('org', ''),
                        'as': data.get('as', ''),
                        'asname': data.get('asname', ''),
                        'reverse': data.get('reverse', ''),
                        'mobile': data.get('mobile', False),
                        'proxy': data.get('proxy', False),
                        'hosting': data.get('hosting', False),
                        'query': data.get('query', '')
                    }
        except Exception as e:
            logger.warning(f"ip-api.com failed: {str(e)}")
        return None
    
    def _fetch_from_ipinfo(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Fetch data from ipinfo.io"""
        try:
            response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=3)
            if response.status_code == 200:
                data = response.json()
                loc = data.get('loc', '').split(',')
                lat = float(loc[0]) if loc[0] else 0
                lon = float(loc[1]) if len(loc) > 1 and loc[1] else 0
                
                return {
                    'source': 'ipinfo.io',
                    'ip': ip_address,
                    'hostname': data.get('hostname', ''),
                    'city': data.get('city', ''),
                    'region': data.get('region', ''),
                    'country': data.get('country', ''),
                    'country_name': self._get_country_name(data.get('country', '')),
                    'loc': data.get('loc', ''),
                    'lat': lat,
                    'lon': lon,
                    'org': data.get('org', ''),
                    'postal': data.get('postal', ''),
                    'timezone': data.get('timezone', ''),
                    'company': data.get('company', {}),
                    'privacy': data.get('privacy', {}),
                    'domains': data.get('domains', {}),
                    'asn': data.get('asn', {}),
                    'anycast': data.get('anycast', False)
                }
        except Exception as e:
            logger.warning(f"ipinfo.io failed: {str(e)}")
        return None
    
    def _fetch_from_ipgeolocation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Fetch data from ipgeolocation.io (requires API key)"""
        try:
            # You need to get a free API key from https://ipgeolocation.io/
            API_KEY = ""  # Add your API key here
            
            if API_KEY:
                response = requests.get(
                    f'https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={ip_address}',
                    timeout=3
                )
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        'source': 'ipgeolocation.io',
                        'ip': ip_address,
                        'continent_name': data.get('continent_name', ''),
                        'country_name': data.get('country_name', ''),
                        'country_code2': data.get('country_code2', ''),
                        'country_code3': data.get('country_code3', ''),
                        'state_prov': data.get('state_prov', ''),
                        'district': data.get('district', ''),
                        'city': data.get('city', ''),
                        'zipcode': data.get('zipcode', ''),
                        'latitude': data.get('latitude', ''),
                        'longitude': data.get('longitude', ''),
                        'is_eu': data.get('is_eu', False),
                        'calling_code': data.get('calling_code', ''),
                        'country_tld': data.get('country_tld', ''),
                        'languages': data.get('languages', ''),
                        'country_flag': data.get('country_flag', ''),
                        'isp': data.get('isp', ''),
                        'connection_type': data.get('connection_type', ''),
                        'organization': data.get('organization', ''),
                        'geoname_id': data.get('geoname_id', ''),
                        'currency': data.get('currency', {}),
                        'time_zone': data.get('time_zone', {})
                    }
        except Exception as e:
            logger.warning(f"ipgeolocation.io failed: {str(e)}")
        return None
    
    def _get_country_name(self, country_code: str) -> str:
        """Convert country code to country name"""
        countries = {
            'US': 'United States',
            'GB': 'United Kingdom',
            'CA': 'Canada',
            'AU': 'Australia',
            'IN': 'India',
            'BD': 'Bangladesh',
            # Add more as needed
        }
        return countries.get(country_code, country_code)
    
    def get_ip_info(self, ip_address: str) -> Dict[str, Any]:
        """Get comprehensive IP information from multiple sources"""
        
        # First, validate IP address
        if not self._validate_ip(ip_address):
            return {'error': 'Invalid IP address format'}
        
        result = {
            'ip': ip_address,
            'timestamp': datetime.utcnow().isoformat(),
            'sources': [],
            'data': {}
        }
        
        # Try each service
        for service in self.services:
            try:
                data = service(ip_address)
                if data:
                    source = data.pop('source')
                    result['sources'].append(source)
                    result['data'][source] = data
            except Exception as e:
                logger.error(f"Service error: {str(e)}")
        
        # If no data found
        if not result['sources']:
            result['error'] = 'Could not fetch IP information from any source'
        
        return result
    
    def _validate_ip(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            socket.inet_pton(socket.AF_INET, ip_address)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, ip_address)
                return True
            except socket.error:
                return False

# Initialize service
ip_service = IPInfoService()

@app.route('/api/v1/ip', methods=['GET'])
def get_ip_info():
    """
    Get detailed information about an IP address
    Query parameter: ip (optional, defaults to client IP)
    """
    ip_address = request.args.get('ip')
    
    # If no IP provided, use client IP
    if not ip_address:
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            ip_address = forwarded.split(',')[0].strip()
        else:
            ip_address = request.remote_addr
    
    logger.info(f"Fetching info for IP: {ip_address}")
    
    # Get IP information
    ip_data = ip_service.get_ip_info(ip_address)
    
    # Add request metadata
    ip_data['request'] = {
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(ip_data)

@app.route('/api/v1/myip', methods=['GET'])
def get_my_ip():
    """Get information about the client's own IP address"""
    # Get client IP
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        client_ip = forwarded.split(',')[0].strip()
    else:
        client_ip = request.remote_addr
    
    ip_data = ip_service.get_ip_info(client_ip)
    
    return jsonify({
        'your_ip': client_ip,
        'info': ip_data,
        'headers': {
            'user_agent': request.headers.get('User-Agent'),
            'accept_language': request.headers.get('Accept-Language'),
            'x_forwarded_for': request.headers.get('X-Forwarded-For')
        }
    })

@app.route('/api/v1/bulk', methods=['POST'])
def bulk_ip_lookup():
    """
    Bulk IP lookup
    Request body: {"ips": ["8.8.8.8", "1.1.1.1"]}
    Maximum 10 IPs per request
    """
    try:
        data = request.get_json()
        
        if not data or 'ips' not in data:
            return jsonify({'error': 'No IPs provided'}), 400
        
        ips = data['ips']
        
        if not isinstance(ips, list):
            return jsonify({'error': 'IPs should be a list'}), 400
        
        if len(ips) > 10:
            return jsonify({'error': 'Maximum 10 IPs allowed per request'}), 400
        
        results = []
        for ip in ips:
            if ip_service._validate_ip(ip):
                info = ip_service.get_ip_info(ip)
                results.append({
                    'ip': ip,
                    'info': info
                })
            else:
                results.append({
                    'ip': ip,
                    'error': 'Invalid IP address format'
                })
        
        return jsonify({
            'count': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Bulk lookup error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/validate', methods=['GET'])
def validate_ip():
    """Validate if an IP address is valid"""
    ip_address = request.args.get('ip')
    
    if not ip_address:
        return jsonify({'error': 'IP address required'}), 400
    
    is_valid = ip_service._validate_ip(ip_address)
    
    return jsonify({
        'ip': ip_address,
        'valid': is_valid,
        'type': self._get_ip_type(ip_address) if is_valid else None
    })

def _get_ip_type(ip_address: str) -> str:
    """Determine IP address type"""
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
        return 'IPv4'
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip_address)
            return 'IPv6'
        except socket.error:
            return 'Invalid'

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'IP Information API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': 'running'
    })

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get API statistics"""
    return jsonify({
        'endpoints': {
            '/api/v1/ip': 'Get IP information',
            '/api/v1/myip': 'Get client IP information',
            '/api/v1/bulk': 'Bulk IP lookup (POST)',
            '/api/v1/validate': 'Validate IP address',
            '/api/v1/health': 'Health check',
            '/api/v1/stats': 'API statistics'
        },
        'services': ['ip-api.com', 'ipinfo.io', 'ipgeolocation.io'],
        'rate_limit': '100 requests per hour',
        'bulk_limit': '10 IPs per request'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    # Configuration
    host = '0.0.0.0'
    port = 5000
    debug = True
    
    print("=" * 60)
    print("IP Information API")
    print("=" * 60)
    print(f"Server running on: http://{host}:{port}")
    print("\nAvailable Endpoints:")
    print("  GET  /api/v1/ip?ip=8.8.8.8       - Get IP information")
    print("  GET  /api/v1/myip                - Get your IP information")
    print("  POST /api/v1/bulk                - Bulk IP lookup")
    print("  GET  /api/v1/validate?ip=8.8.8.8 - Validate IP")
    print("  GET  /api/v1/health              - Health check")
    print("  GET  /api/v1/stats               - API statistics")
    print("\nExamples:")
    print("  curl http://localhost:5000/api/v1/ip?ip=8.8.8.8")
    print("  curl http://localhost:5000/api/v1/myip")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)
