#!/usr/bin/env python3
"""
Simple mock API server for performance testing using FastAPI
"""
import json
import time
import uuid as _uuid_mod
from typing import Optional
from fastapi import FastAPI, HTTPException

app = FastAPI()

# In-memory posts store
_posts = {}
_next_id = 1


@app.get("/get")
def get_get():
    return {
        'url': 'http://localhost:8000/get',
        'method': 'GET',
        'timestamp': time.time(),
        'data': {'message': 'Mock GET response'}
    }


@app.get("/json")
def get_json():
    return {
        'slideshow': {
            'author': 'Mock API',
            'date': '2024',
            'slides': [{'title': 'Mock Slide', 'type': 'text'}]
        }
    }


@app.get("/uuid")
def get_uuid():
    return {'uuid': str(_uuid_mod.uuid4())}


@app.post("/post")
def post_post(data: dict):
    return {
        'url': 'http://localhost:8000/post',
        'method': 'POST',
        'timestamp': time.time(),
        'data': {'message': 'Mock POST response', 'created': True, 'received': data}
    }


@app.get("/posts")
def list_posts():
    return list(_posts.values())


@app.post("/posts")
def create_post(data: dict):
    global _next_id
    post_id = _next_id
    _next_id += 1
    post = {**data, 'id': post_id}
    _posts[post_id] = post
    return post


@app.get("/posts/{post_id}")
def get_post(post_id: int):
    if post_id not in _posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return _posts[post_id]


@app.put("/posts/{post_id}")
def update_post(post_id: int, data: dict):
    if post_id not in _posts:
        raise HTTPException(status_code=404, detail="Post not found")
    _posts[post_id] = {**data, 'id': post_id}
    return _posts[post_id]


@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    if post_id not in _posts:
        raise HTTPException(status_code=404, detail="Post not found")
    deleted = _posts.pop(post_id)
    return {'deleted': True, 'id': post_id}


if __name__ == '__main__':
    import uvicorn
    print("Mock API server running on http://localhost:8000", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
