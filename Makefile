ORG_ID = dcn
DOCKER_IMAGE = python36-django-env
DOCKER_NETWORK = nave_network
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
	docker run -it --rm $(COMMON_RUN_FLAGS) $(DOCKER_IMAGE) python manage.py runserver

# Open Django shell
shell:
	docker run -it --rm $(COMMON_RUN_FLAGS) $(DOCKER_IMAGE) python manage.py shell


migrate:
	docker run -it --rm $(COMMON_RUN_FLAGS) $(DOCKER_IMAGE) python manage.py migrate
