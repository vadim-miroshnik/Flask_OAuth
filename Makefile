run_environment:
	cp .env.example .env
	# COMPOSE_PROJECT_NAME используется для именования volumes
	COMPOSE_PROJECT_NAME=auth docker-compose up -d redis postgres pgadmin jaeger

run_service:
	COMPOSE_PROJECT_NAME=auth docker-compose up --build auth

run_tests:
	COMPOSE_PROJECT_NAME=auth docker-compose up --build tests

destroy_db:
	docker stop postgres_container && docker rm --force postgres_container
	docker volume rm auth_postgres

install_requirements:
	pip3 install -r src/requirements.txt

build:
	docker-compose build

run_server:
	python3 src/pywsgi.py

down:
	COMPOSE_PROJECT_NAME=auth docker-compose down

prod_run:
	COMPOSE_PROJECT_NAME=auth_prod docker-compose -f docker-compose.yml up -d --build

prod_down:
	COMPOSE_PROJECT_NAME=auth_prod docker-compose -f docker-compose.yml down