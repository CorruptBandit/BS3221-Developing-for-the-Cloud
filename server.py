#!/usr/bin/env python3

from pathlib import Path
from typing import List, Optional

from fastapi import Body, Request, status
from fastapi_offline import FastAPIOffline
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
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
    dog_walker: bool

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
    # Update the MongoDB document to set the dog_walker field
    users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
    if dogs:
        for dog in dogs:
            await save_dog(dog)
    return RedirectResponse(f"{config['proxy_path']}/user?email={user.email}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/login", include_in_schema=False)
async def login(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):

    await save_user(user)


    stored_user = users_collection.find_one({"email": user.email})
    if user.password != stored_user["password"]:
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
    uvicorn.run(app, host=config["fastapi_host"], port=config["fastapi_port"])


if __name__ == "__main__":
    main()
