# BS3221-Developing-for-the-Cloud
Working prototype of the Cloud Full Stack Implementation with: •  Permanent, external Web address • The (rudimentary) Waqq.ly front-end to register pets, and to register dog walkers • The microservices-orientated backend storing the above data in a noSQL database • A RESTful API for the backend and the frontend to talk to each other

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/


https://pentacent.medium.com/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71

https://github.com/wmnnd/nginx-certbot

sudo cat /etc/letsencrypt/live/legsmuttsmove.co.uk/fullchain.pem /etc/letsencrypt/live/legsmuttsmove.co.uk/privkey.pem > mongodb.pem
sudo chmod 644 mongodb.pem
sudo mv mongodb.pem /etc/ssl/mongodb.pem
