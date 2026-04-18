from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class PostData(BaseModel):
    title: str
    body: str
    userId: int

# Fake in-memory DB
posts = {
    1: {"id": 1, "title": "Hello from API", "body": "Test body", "userId": 1}
}

@app.get("/posts")
def list_posts():
    return list(posts.values())

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts[post_id]

@app.post("/posts")
def create_post(data: PostData):
    new_id = max(posts.keys()) + 1
    posts[new_id] = {"id": new_id, **data.dict()}
    return posts[new_id]

@app.put("/posts/{post_id}")
def update_post(post_id: int, data: PostData):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")
    posts[post_id] = {"id": post_id, **data.dict()}
    return posts[post_id]

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")
    deleted = posts.pop(post_id)
    return {"deleted": deleted}