from typing import Optional

import uvicorn as uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


class Blog(BaseModel):
    title: str
    body: str
    published: bool


app = FastAPI()


@app.get('/blog')
def limiting(limit=10, published: bool = True, sort: Optional[str] = None):
    if published:
        return {'data': f'{limit} published  from the database'}
    else:
        return {'data': f'{limit} blogs from the db'}


@app.get('/blog/{id}')
def index(id: int):
    return {'data': id}


@app.get('/blog/{id}/comments')
def comments(id, limit=10):
    return {'data': {'1', '2'}}


@app.post('/blog')
def create_blog(blog: Blog):
    return {'data': f"Blog is created with {blog.title} as title"}
#
#
# # uvicorn main:app --reload
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
