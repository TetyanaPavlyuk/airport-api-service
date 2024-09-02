# Airport API Service
> API service for airport management written on DRF

System of managing airplanes, flights, crew and routes. 
This system will allow travellers to easily book tickets for 
upcoming trips using airplanes.

## Installing using GitHub

Install PostgreSQL and create db

```shell
git clone https://github.com/TetyanaPavlyuk/airport-api-service.git
cd airport_api_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
set POSTGRES_HOST=<your_db_host_name>
set POSTGRES_DB=<your_db_name>
set POSTGRES_USER=<your_db_username>
set POSTGRES_PASSWORD=<your_db_password>
set SECRET_KEY=<your_secret_key>
python manage.py migrate
python manage.py runserver
```

## Run with Docker

Docker should be installed

```shell
docker-compose build
docker-compose up
```

## Getting Access

Install PostgreSQL and create db
* Create user via /api/user/register/
* Get access token via /api/user/token/

## Features

* JWT authenticated
* Admin panel /admin/
* Documentation is located at /api/doc/swagger-ui/
* Managing orders and tickets for authenticated users
* Only admin can create and view crew and crew positions
* Only admin can create flights, airplanes, airplane types, 
airplane manufacturers, routes, airports
* Authenticated users can view flights, airplanes, airplane 
types, airplane manufacturers, routes, airports
* Filtering flights
