#!/usr/bin/env python3

"""Backend for a Dog Walker Service"""

from pathlib import Path
from typing import List, Optional
import os
import subprocess

from fastapi import Body, Request, status
from fastapi_offline import FastAPIOffline
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import bcrypt
import certifi
import markdown
import uvicorn


SCRIPT_DIR = Path(__file__).resolve().parent

config = {
    "fastapi_host": os.environ.get("FASTAPI_HOST", "0.0.0.0"),
    "fastapi_port": int(os.environ.get("FASTAPI_PORT", 8080)),
    "proxy_path": os.environ.get("PROXY_PATH", ""),
    "cert_file": os.environ.get("CERT_FILE", "/etc/letsencrypt/live/legsmuttsmove.co.uk/fullchain.pem"),
    "key_file": os.environ.get("KEY_FILE", "/etc/letsencrypt/live/legsmuttsmove.co.uk/privkey.pem"),
    "mongo_uri": os.environ.get("MONGO_URI", "mongodb://mongodb:27017")
}

app = FastAPIOffline(
    title="Backend",
    description="API to talk to MongoDB",
    root_path="",
    version = "development",
    docs_url=None
)

client = MongoClient(
    config["mongo_uri"], 
    server_api=ServerApi("1"),
    tls=True,
    tlsAllowInvalidHostnames=True  # To-Do: Fix this to only allow legsmuttsmove.co.uk
)
users_collection = client["DogCompany"]["Users"]
dogs_collection = client["DogCompany"]["Dogs"]

template_dir = SCRIPT_DIR / "templates"
templates = Jinja2Templates(directory=template_dir)


# Create a model to represent the user data
class User(BaseModel):
    email: str
    password: str
    dog_walker: bool

# Create a model to represent the dog data
class Dog(BaseModel):
    owner: str
    breed: str
    name: str
    age: str


async def save_user(user: User):
    user.password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    print(user.password)
    users_collection.insert_one(user.model_dump())

async def save_dog(dog: Dog):
    dogs_collection.insert_one(dog.model_dump())


@app.get("", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@app.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_typer():
    return RedirectResponse(f"{config['proxy_path']}/index")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(SCRIPT_DIR / "static" / "images" / "favicon.ico")


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
async def register(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):
    await save_user(user)
    users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
    if dogs:
        for dog in dogs:
            await save_dog(dog)
    return RedirectResponse(f"{config['proxy_path']}/user?email={user.email}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/login", include_in_schema=False)
async def login(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):
    stored_user = users_collection.find_one({"email": user.email})
    if not bcrypt.hashpw(user.password.encode(), stored_user["password"]) == stored_user["password"]:
        return JSONResponse(content={"message": "Invalid password"}, status_code=status.HTTP_401_UNAUTHORIZED)

    # Update the MongoDB document to set the dog_walker field
    users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
    if dogs:
        for dog in dogs:
            await save_dog(dog)
    return RedirectResponse(f"{config['proxy_path']}/user?email={user.email}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/check_user_exists", include_in_schema=False)
async def check_user_exists(email: str):
    user = users_collection.find_one({"email": email})
    if user is not None:
        return True
    else:
        return False


@app.get("/user", include_in_schema=False)
async def get_user(request: Request, email: str):
    user = users_collection.find_one({"email": email})

    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=status.HTTP_404_NOT_FOUND)

    # Get the user's dogs associated with their email
    user_dogs = dogs_collection.find({"owner": email})

    dog_list = []
    for dog in user_dogs:
        dog_list.append({"name": dog["name"], "age": dog["age"], "breed": dog["breed"]})

    template_name = "user_info.html"

    # Determine if the user is a dog walker
    is_dog_walker = user.get("dog_walker", False)

    # Set the context variables
    template_context = {"request": request, "email": email, "is_dog_walker": is_dog_walker, "dogs": dog_list}

    return templates.TemplateResponse(template_name, template_context)


def main():
    uvicorn.run(
        app,
        host=config["fastapi_host"],
        port=config["fastapi_port"],
        ssl_certfile=config["cert_file"],
        ssl_keyfile=config["key_file"]
    )


if __name__ == "__main__":
    main()
