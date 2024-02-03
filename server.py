#!/usr/bin/env python3

"""Backend for a Dog Walker Service"""

from datetime import timedelta
from pathlib import Path
from typing import List, Optional
import os
import subprocess

from fastapi import Body, Request, Security, status
from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessCookie
from fastapi_offline import FastAPIOffline
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
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
    "mongo_uri": os.environ.get("MONGO_URI", "mongodb://legsmuttsmove.co.uk:27017"),
    "jwt_secret_key": os.environ.get("JWT_SECRET_KEY", "insecure")
}

app = FastAPIOffline(
    title="Backend",
    description="API to talk to MongoDB",
    root_path="",
    version = "development",
    docs_url=None
)

access_security = JwtAccessCookie(
    secret_key=config["jwt_secret_key"], 
    auto_error=True, 
    access_expires_delta=timedelta(minutes=15)
)

client = MongoClient(
    config["mongo_uri"], 
    server_api=ServerApi("1"),
    tls=True,
)

users_collection = client["DogCompany"]["Users"]
dogs_collection = client["DogCompany"]["Dogs"]

app.mount("/static", StaticFiles(directory="static"), name="static")
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
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    user.password = hashed_password.decode()  # Convert bytes to string
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
async def register(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):
    await save_user(user)
    users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
    if dogs:
        for dog in dogs:
            await save_dog(dog)
    subject = {"email": user.email}
    access_token = access_security.create_access_token(subject=subject)
    return JSONResponse(content={"access_token_cookie": access_token}, status_code=status.HTTP_200_OK)


@app.post("/login", include_in_schema=False)
async def login(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):
    stored_user = users_collection.find_one({"email": user.email})
    
    if stored_user and bcrypt.checkpw(user.password.encode(), stored_user["password"].encode()):
        # Passwords match, continue with login
        users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
        
        if dogs:
            for dog in dogs:
                await save_dog(dog)
        
        subject = {"email": user.email}
        access_token = access_security.create_access_token(subject=subject)
        return JSONResponse(content={"access_token_cookie": access_token}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"message": "Invalid email or password"}, status_code=status.HTTP_401_UNAUTHORIZED)



@app.get("/check_user_exists", include_in_schema=False)
async def check_user_exists(email: str):
    user = users_collection.find_one({"email": email})
    if user is not None:
        return True
    else:
        return False


@app.get("/user", include_in_schema=False)
async def get_user(request: Request, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user = users_collection.find_one({"email": credentials["email"]})
    user_dogs = dogs_collection.find({"owner": credentials["email"]})

    dog_list = []
    for dog in user_dogs:
        dog_list.append({"name": dog["name"], "age": dog["age"], "breed": dog["breed"]})

    # Determine if the user is a dog walker
    is_dog_walker = user.get("dog_walker", False)
    # Set the context variables
    template_context = {"request": request, "email": credentials["email"], "is_dog_walker": is_dog_walker, "dogs": dog_list}
    return templates.TemplateResponse("user_info.html", template_context)


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
