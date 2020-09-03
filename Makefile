migrations:
	docker-compose run web python manage.py makemigrations main

migrate:
	docker-compose run web python manage.py migrate

compilescss:
	docker-compose run web python manage.py compilescss

shell:
	docker-compose run web python manage.py shell

flake8:
	docker-compose run web flake8 $(file)

up:
	docker-compose up

down:
	docker-compose down

build:
	docker-compose build

elevate:
	docker-compose run web python manage.py elevate_sso_user_permissions

collectstatic:
	docker-compose run web python manage.py collectstatic

dev-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/dev.txt requirements.in/dev.in

prod-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/prod.txt requirements.in/prod.in
