#!/usr/bin/env python3

from pathlib import Path
from typing import List, Optional

from fastapi import Form, Request, status
from fastapi_offline import FastAPIOffline
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
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
    "proxy_path": "",  # Empty string if not behind a reverse proxy

}

template_dir = SCRIPT_DIR / "templates"
templates = Jinja2Templates(directory=template_dir)

# Create a model to represent the user data
class UserData:
    def __init__(self, email, password, pets=None):
        self.email = email
        self.password = password
        self.pets = pets if pets is not None else []

# Create a model to represent the pet data
class PetData:
    def __init__(self, type, name, age):
        self.type = type
        self.name = name
        self.age = age


def mongo_connect():
    uri = "mongodb+srv://University:Winchester123@bs3221.gurmf48.mongodb.net/?retryWrites=true&w=majority"
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client["PetCompany"]

@app.get("", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@app.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_typer():
    return RedirectResponse(f"{config['proxy_path']}/readme")


@app.get("/readme", response_class=HTMLResponse,
         status_code=status.HTTP_200_OK,
         summary="Return markdown of readme",
         include_in_schema=False)
async def index(request: Request):
    with open(SCRIPT_DIR / "README.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()

    html = markdown.markdown(text, extensions=['tables'])
    data = {
        "text": html
    }
    return templates.TemplateResponse("/index.html", context={"request": request})


@app.get("/status", include_in_schema=False)
async def get_status():
    """
    Assert webserver is running

    Return status code
    """
    return 200

@app.post("/register", include_in_schema=False)
@app.post("/register", include_in_schema=False)
async def process_registration(
    email: str = Form(...),
    password: str = Form(...),
    petData: Optional[List[dict]] = Form(None)
):
    db = mongo_connect()
    pets = []

    if petData:
        for pet_item in petData:
            pet_type = pet_item.get("type", "")
            pet_name = pet_item.get("name", "")
            pet_age = pet_item.get("age", 0)
            pet = PetData(pet_type, pet_name, pet_age)
            pets.append(pet)

    # Create the user data
    user_data = UserData(email, password, pets)

    # Store user data in the Users collection
    users_collection = db["Users"]
    user_id = users_collection.insert_one(user_data.__dict__).inserted_id

    # Store pet data in the Pets collection
    pets_collection = db["Pets"]
    for pet in pets:
        pet_data = {"type": pet.type, "name": pet.name, "age": pet.age, "user_id": user_id}
        pets_collection.insert_one(pet_data)

    return {"message": "Registration successful!", "user": user_data.__dict__}


@app.get("/user", include_in_schema=False)
async def get_user():
    """
    Assert user credentials

    Return user details
    """
    return 200


def main():
    uvicorn.run(app, host=config["fastapi_host"], port=config["fastapi_port"])


if __name__ == "__main__":
    main()
