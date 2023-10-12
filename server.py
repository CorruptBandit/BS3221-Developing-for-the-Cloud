#!/usr/bin/env python3

from pathlib import Path
from typing import List, Optional

from fastapi import Body, Request, status
from fastapi_offline import FastAPIOffline
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
import markdown
import uvicorn


SCRIPT_DIR = Path(__file__).resolve().parent

app = FastAPIOffline(
    title="Backend",
    description="API to talk to MongoDB",
    root_path="",
    version = "development",
    docs_url=None
)

config = {
    "fastapi_host": "0.0.0.0",
    "fastapi_port": 8080,
    "proxy_path" : ""
}

template_dir = SCRIPT_DIR / "templates"
templates = Jinja2Templates(directory=template_dir)

# Create a model to represent the user data
class User(BaseModel):
    email: str
    password: str

# Create a model to represent the dog data
class Dog(BaseModel):
    owner: str
    breed: str
    name: str
    age: str

uri = "mongodb+srv://University:Winchester123@bs3221.gurmf48.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())
# Send a ping to confirm a successful connection


users_collection = client["DogCompany"]["Users"]
dogs_collection = client["DogCompany"]["Dogs"]

async def save_user(user: User):
    users_collection.insert_one(user.model_dump())

async def save_dog(dog: Dog):
    dogs_collection.insert_one(dog.model_dump())

@app.get("", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@app.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_typer():
    return RedirectResponse(f"{config['proxy_path']}/index")


@app.get("/index", response_class=HTMLResponse,
         status_code=status.HTTP_200_OK,
         summary="Return the index.html",
         include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse("/index.html", context={"request": request})

@app.get("/status", include_in_schema=False)
async def get_status():
    """
    Assert webserver is running

    Return status code
    """
    return 200

@app.post("/register", include_in_schema=False)
async def register(user: User = Body(...), dogs: List[Dog] = Body(...)):
    await save_user(user)
    for dog in dogs:
        await save_dog(dog)


@app.post("/check_user_exists", include_in_schema=False)
async def validate(user: User = Body(...), dogs: List[Dog] = Body(...)):
    user = users_collection.find_one({"email": email})
    if not user:
        return False
    else:
        return True

@app.get("/user", include_in_schema=False)
async def get_user(request: Request, email: str):
    """
    Get user details and their dogs
    """
    user = users_collection.find_one({"email": email})

    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=status.HTTP_404_NOT_FOUND)

    # Get the user's dogs associated with their email
    user_dogs = dogs_collection.find({"owner": email})

    dog_list = []
    for dog in user_dogs:
        dog_list.append({"name": dog["name"], "age": dog["age"], "breed": dog["breed"]})

    return templates.TemplateResponse("user_info.html", {"request": request, "email": email, "dogs": dog_list})


def main():
    uvicorn.run(app, host=config["fastapi_host"], port=config["fastapi_port"])


if __name__ == "__main__":
    main()
