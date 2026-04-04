#!/usr/bin/env python3
"""
Simple mock API server for performance testing
"""
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class MockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/get':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'url': 'http://localhost:8080/get',
                'method': 'GET',
                'timestamp': time.time(),
                'data': {'message': 'Mock GET response'}
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'slideshow': {
                    'author': 'Mock API',
                    'date': '2024',
                    'slides': [{'title': 'Mock Slide', 'type': 'text'}]
                }
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/uuid':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'uuid': '12345678-1234-1234-1234-123456789abc'}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def do_POST(self):
        if self.path == '/post':
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'url': 'http://localhost:8080/post',
                'method': 'POST',
                'timestamp': time.time(),
                'data': {'message': 'Mock POST response', 'created': True}
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def log_message(self, format, *args):
        # Suppress default logging to reduce noise
        pass

def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, MockAPIHandler)
    print("Mock API server running on http://localhost:8080")
    httpd.serve_forever()

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped")