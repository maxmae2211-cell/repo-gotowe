from fastapi import FastAPI

app = FastAPI()

@app.get("/get")
def get_post():
    return {"message": "ok"}

@app.post("/post")
def create_post(data: dict):
    return {"received": data}