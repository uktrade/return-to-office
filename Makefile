flake8:
	.venv/bin/python -m flake8

black:
	.venv/bin/python -m black --check .

black_format:
	.venv/bin/python -m black .

setup:
	scripts/initial-setup.sh
	make migrations migrate
	make compilescss
	make collectstatic

migrations:
	docker-compose run --rm web python manage.py makemigrations main

migrate:
	docker-compose run --rm web python manage.py migrate

axes_reset:
	docker-compose run --rm web python manage.py axes_reset

compilescss:
	docker-compose run --rm web python manage.py compilescss

shell:
	docker-compose run --rm web python manage.py shell

psql:
	PGPASSWORD=password psql -h localhost -U postgres rto

docker_flake8:
	docker-compose run --rm web flake8

docker_black:
	docker-compose run --rm web black --check .

pip-check:
	docker-compose run --rm web pip-check

up:
	docker-compose up

down:
	docker-compose down

build:
	docker-compose build

elevate:
	docker-compose run --rm web python manage.py elevate_sso_user_permissions

collectstatic:
	docker-compose run --rm web python manage.py collectstatic --noinput

dev-requirements:
	docker-compose run --rm web pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm web pip-compile --output-file requirements/dev.txt requirements.in/dev.in

prod-requirements:
	docker-compose run --rm web pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm web pip-compile --output-file requirements/prod.txt requirements.in/prod.in

all-requirements:
	docker-compose run --rm web pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm web pip-compile --output-file requirements/dev.txt requirements.in/dev.in
	docker-compose run --rm web pip-compile --output-file requirements/prod.txt requirements.in/prod.in

test:
	docker-compose run --rm web pytest

superuser:
	docker-compose run --rm web python manage.py createsuperuser
