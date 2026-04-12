from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PostData(BaseModel):
    title: str
    body: str
    userId: int

@app.get("/get")
def get_post():
    return {"message": "ok"}

@app.post("/post")
def create_post(data: PostData):
    return {"received": data}
