#!/usr/bin/env python3

"""
Backend for the Dog Walker Service.
This script initialises a FastAPI application to serve as the backend for a service that connects dog owners with dog walkers. 
It includes endpoints for user registration, login, and fetching user information, alongside dog details. 
The application utilises MongoDB for data storage and employs JWT for secure access.
"""

from datetime import timedelta
from pathlib import Path
import os
import bcrypt

from fastapi import FastAPIOffline, Body, Request, Security, status
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_jwt import JwtAccessCookie
from pydantic import BaseModel
from pymongo import MongoClient, server_api
import uvicorn


# Define the script directory for relative file paths
SCRIPT_DIR = Path(__file__).resolve().parent

# Configuration settings from environment variables or default values
config = {
    "fastapi_host": os.environ.get("FASTAPI_HOST", "0.0.0.0"),
    "fastapi_port": int(os.environ.get("FASTAPI_PORT", 8080)),
    "proxy_path": os.environ.get("PROXY_PATH", ""),
    "cert_file": os.environ.get("CERT_FILE", "/etc/letsencrypt/live/example.co.uk/fullchain.pem"),
    "key_file": os.environ.get("KEY_FILE", "/etc/letsencrypt/live/example.co.uk/privkey.pem"),
    "mongo_uri": os.environ.get("MONGO_URI", "mongodb://example.co.uk:27017"),
    "jwt_secret_key": os.environ.get("JWT_SECRET_KEY", "insecure")
}

# Initialise the FastAPI application with offline access and no documentation URL
app = FastAPIOffline(
    title="Backend",
    description="API to communicate with MongoDB",
    root_path="",
    version="development",
    docs_url=None
)

# Setup JWT access security with a secret key and a 15-minute expiration
access_security = JwtAccessCookie(
    secret_key=config["jwt_secret_key"], 
    auto_error=True, 
    access_expires_delta=timedelta(minutes=15)
)

# Connect to the MongoDB client securely with TLS
client = MongoClient(
    config["mongo_uri"], 
    server_api=ServerApi("1"),
    tls=True,
)

# Define MongoDB collections for users and dogs
users_collection = client["DogCompany"]["Users"]
dogs_collection = client["DogCompany"]["Dogs"]

# Mount static files to the '/static' path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates directory
template_dir = SCRIPT_DIR / "templates"
templates = Jinja2Templates(directory=template_dir)


# Models for user and dog data using Pydantic for data validation
class User(BaseModel):
    email: str
    password: str
    dog_walker: bool


class Dog(BaseModel):
    owner: str
    breed: str
    name: str
    age: str


# Utility function to save a user to the MongoDB database
async def save_user(user: User):
    """Hashes the user's password and saves the user to the database."""
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    user.password = hashed_password.decode()  # Convert bytes to string
    users_collection.insert_one(user.dict())


# Utility function to save a dog to the MongoDB database
async def save_dog(dog: Dog):
    """Saves the dog details to the database."""
    dogs_collection.insert_one(dog.dict())


# Route to redirect the root URL to the index page
@app.get("", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@app.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_to_index():
    """Redirects requests to the root URL to the index page."""
    return RedirectResponse(url=f"{config['proxy_path']}/index")


# Route to serve the index.html page
@app.get("/index", response_class=HTMLResponse, status_code=status.HTTP_200_OK, summary="Return the index.html", include_in_schema=False)
async def index(request: Request):
    """Renders and returns the index.html page.
    
    Returns:
        TemplateResponse: The index page templated with Jinja
    """
    return templates.TemplateResponse("index.html", {"request": request})


# Route to check status
@app.get("/status", include_in_schema=False)
async def get_status():
    """Check if the web server is operational.

    Returns:
        int: The HTTP status code indicating the server is operational.
    """
    return 200


# Route to register
@app.post("/register", include_in_schema=False)
async def register(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):
    """
    Registers a new user and optionally their dogs.

    Args:
        user (User): The user details to register.
        dogs (Optional[List[Dog]]): A list of dogs belonging to the user, if any.

    Returns:
        JSONResponse: A response with the access token cookie upon successful registration.
    """
    # Save the user to the database
    await save_user(user)
    # Update the user's dog walker status
    users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
    # If there are dogs, save them too
    if dogs:
        for dog in dogs:
            await save_dog(dog)
    # Create an access token for the user
    subject = {"email": user.email}
    access_token = access_security.create_access_token(subject=subject)
    # Return the access token in a JSON response
    return JSONResponse(content={"access_token_cookie": access_token}, status_code=status.HTTP_200_OK)


# Route to login
@app.post("/login", include_in_schema=False)
async def login(user: User = Body(...), dogs: Optional[List[Dog]] = Body([])):
    """
    Authenticates a user and logs them in.

    Args:
        user (User): The user attempting to log in.
        dogs (Optional[List[Dog]]): Not directly used for login but can be included for extended functionality.

    Returns:
        JSONResponse: A response indicating the outcome of the login attempt.
    """
    # Retrieve the stored user details from the database
    stored_user = users_collection.find_one({"email": user.email})
    
    # Check if the password matches
    if stored_user and bcrypt.checkpw(user.password.encode(), stored_user["password"].encode()):
        # Update the user's dog walker status
        users_collection.update_one({"email": user.email}, {"$set": {"dog_walker": user.dog_walker}})
        # Save any dogs associated with the user
        if dogs:
            for dog in dogs:
                await save_dog(dog)
        # Create an access token for the user
        subject = {"email": user.email}
        access_token = access_security.create_access_token(subject=subject)
        # Return the access token in a JSON response
        return JSONResponse(content={"access_token_cookie": access_token}, status_code=status.HTTP_200_OK)
    else:
        # Return an error if the email or password is incorrect
        return JSONResponse(content={"message": "Invalid email or password"}, status_code=status.HTTP_401_UNAUTHORIZED)


# Route to check if a user exists
@app.get("/check_user_exists", include_in_schema=False)
async def check_user_exists(email: str):
    """
    Checks if a user exists based on their email address.

    Args:
        email (str): The email address to check.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    # Look for the user in the database
    user = users_collection.find_one({"email": email})
    # Return True if found, False otherwise
    return user is not None


# Route to users data
@app.get("/user", include_in_schema=False)
async def get_user(request: Request, credentials: JwtAuthorizationCredentials = Security(access_security)):
    """
    Retrieves information about the logged-in user.

    Args:
        request (Request): The request object.
        credentials (JwtAuthorizationCredentials): The JWT credentials of the user.

    Returns:
        TemplateResponse: Renders the user's information in a template.
    """
    # Find the user and their dogs in the database
    user = users_collection.find_one({"email": credentials["email"]})
    user_dogs = dogs_collection.find({"owner": credentials["email"]})
    
    # Compile the list of dogs
    dog_list = [{"name": dog["name"], "age": dog["age"], "breed": dog["breed"]} for dog in user_dogs]
    
    # Prepare context for the template
    template_context = {"request": request, "email": credentials["email"], "is_dog_walker": user.get("dog_walker", False), "dogs": dog_list}
    # Render the template with the user's information
    return templates.TemplateResponse("user_info.html", template_context)


# Entrypoint
def main():
    """
    Runs the FastAPI app with Uvicorn, using SSL certificates for HTTPS.
    """
    uvicorn.run(
        app,
        host=config["fastapi_host"],
        port=config["fastapi_port"],
        ssl_certfile=config["cert_file"],
        ssl_keyfile=config["key_file"]
    )


if __name__ == "__main__":
    main()
