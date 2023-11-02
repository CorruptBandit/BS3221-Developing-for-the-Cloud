# BS3221-Developing-for-the-Cloud

This repository contains a working prototype of a Cloud Full Stack Implementation, featuring:

- A permanent, external web address
- A rudimentary front-end, Waqq.ly, for pet registration and dog walker registration
- A microservices-oriented backend that stores data in a NoSQL database
- A RESTful API for communication between the backend and frontend

The live website can be found at [www.legsmuttsmove.co.uk](https://www.legsmuttsmove.co.uk)

The web server is powered by Python and the server script can be located in [server.py](./server.py). The web pages are constructed with HTML, CSS, and JavaScript, which can be found in both the [static directory](./static/) and the [templates directory](./templates/). Everything runs within a Docker environment, and you can access the configuration in the [Dockerfile](./Dockerfile) and [Docker Compose](./compose.yaml) files.

This project leverages the following technologies and tools:
1. Docker
2. NGINX
3. MongoDB
4. Python FastAPI
5. Vanilla JavaScript
6. HTML
7. CSS

## Guide

This guide is how to run the working prototype of a Cloud Full Stack Implementation, **Wagg.ly**

### Configuration

1. Copy the [.env.template](./.env.template) file and rename it to `.env`.
2. Populate the `.env` file with the required values.

### Building

To build the project, use the following command:

```bash
docker compose build
```

### Running

To run the project, use the following command:

```bash
docker compose up
```

### TLS (Transport Layer Security)

TLS is enabled by default across the board with NGINX, FastAPI and Mongo, all within Docker, this was achieved with the following steps:

1. Configure the [init-letsencrypt.sh](./init-letsencrypt.sh) script with the required values: `domains` and `email`. 

   **NGINX LetsEncrypt in Docker** provides a detailed guide and a GitHub repository for this process:

   - [**Guide:** NGINX and Let's Encrypt with Docker](https://pentacent.medium.com/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71)
   - [**GitHub Repository:** NGINX Certbot](https://github.com/wmnnd/nginx-certbot)

   The [init-letsencrypt.sh](./init-letsencrypt.sh) script was taken from the GitHub, although has been modfied for the purpose of this project.

1. To configure MongoDB, follow these steps:

   **This is here only as a reference, as these manual steps are not required. The steps are already scripted in [init-letsencrypt.sh](./init-letsencrypt.sh)**

    - Concatenate the Let's Encrypt certificates (fullchain.pem and privkey.pem) by running the following command:

    ```bash
    sudo cat /etc/letsencrypt/live/<url>/fullchain.pem /etc/letsencrypt/live/<url>/privkey.pem > mongodb.pem
    ```

    - Change the permissions of the `mongodb.pem` file:

    ```bash
    sudo chmod 644 mongodb.pem
    ```

   - Move the `mongodb.pem` file to the `/etc/ssl/` directory:

   ```bash
   sudo mv mongodb.pem /etc/ssl/mongodb.pem
   ```

1. Run the script using the following command:

   ```bash
   ./init-letsencrypt.sh
   ```

   This will incorporate the Let's Encrypt certificates into the containers.

1. In the [NGINX Config](./data/nginx/app.conf), ensure the following settings are correctly configured:

   - `ssl_certificate`
   - `ssl_certificate_key_file`

1. Build and Run your deployment

By following these steps and instructions, you can set up your Cloud Full Stack Implementation with TLS security and configure MongoDB for data storage, ensuring a successful deployment.
