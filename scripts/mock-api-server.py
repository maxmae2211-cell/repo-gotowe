#!/usr/bin/env python3
"""
Simple mock API server for performance testing using FastAPI
"""
import json
import time
from fastapi import FastAPI

app = FastAPI()

@app.get("/get")
def get_get():
    response = {
        'url': 'http://localhost:8000/get',
        'method': 'GET',
        'timestamp': time.time(),
        'data': {'message': 'Mock GET response'}
    }
    return response

@app.get("/json")
def get_json():
    response = {
        'slideshow': {
            'author': 'Mock API',
            'date': '2024',
            'slides': [{'title': 'Mock Slide', 'type': 'text'}]
        }
    }
    return response

@app.get("/uuid")
def get_uuid():
    response = {'uuid': '12345678-1234-1234-1234-123456789abc'}
    return response

@app.post("/post")
def post_post(data: dict):
    response = {
        'url': 'http://localhost:8000/post',
        'method': 'POST',
        'timestamp': time.time(),
        'data': {'message': 'Mock POST response', 'created': True, 'received': data}
    }
    return response

if __name__ == '__main__':
    import uvicorn
    print("Mock API server running on http://localhost:8000", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
