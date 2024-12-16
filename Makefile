ORG_ID = dcn
DOCKER_IMAGE = python36-django-env
DOCKER_NETWORK = nave_nave_network
COMMON_RUN_FLAGS = --network=$(DOCKER_NETWORK) \
                   -v "$(PWD)":/app \
                   -w /app \
                   -e DJANGO_SETTINGS_MODULE=nave.projects.$(ORG_ID).settings \
                   -e DATABASE_HOST="postgresql" \
                   -e DATABASE_PORT="5432"

# Build Docker image
build-docker:
	docker build -t $(DOCKER_IMAGE) .

# Run Django server
runserver:
	docker run -it --rm $(COMMON_RUN_FLAGS) -p 8000:8000 $(DOCKER_IMAGE) python manage.py runserver 0.0.0.0:8000

# Open Django shell
shell:
	docker run -it --rm $(COMMON_RUN_FLAGS) $(DOCKER_IMAGE) python manage.py shell


migrate:
	docker run -it --rm $(COMMON_RUN_FLAGS) $(DOCKER_IMAGE) python manage.py migrate
