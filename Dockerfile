# Use the official Python image from Docker Hub
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy your Python application code to the container
COPY ./static/ /app
COPY ./templates/ /app
COPY ./server.py /app
COPY ./requirements.txt /app

# Install required Python packages
RUN pip install -r ./requirements.txt

# Run your FastAPI application using uvicorn
ENTRYPOINT ["python3", "./server.py"]
