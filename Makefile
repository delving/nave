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

#######################
# Deployment Settings #
#######################

# SSH host for deployment (required, set via command line or environment)
# Example: make deploy SSH_HOST=user@server.example.com
SSH_HOST ?=

# Deploy path - can be overridden per project
# Default: /opt/hub3/$(ORG_ID)/nave_app
# DCN staging: /opt/hub3/dcn/staging/nave_app
DEPLOY_PATH ?= /opt/hub3/$(ORG_ID)/nave_app

# User that owns the deployed files (for chown after rsync)
DEPLOY_USER ?= $(ORG_ID)

# Rsync exclude patterns
# NOTE: These patterns prevent rsync --delete from removing server-side files
RSYNC_EXCLUDES = --exclude='.git' \
                 --exclude='__pycache__' \
                 --exclude='*.pyc' \
                 --exclude='.idea' \
                 --exclude='.vagrant' \
                 --exclude='*.log' \
                 --exclude='local_settings.py' \
                 --exclude='gunicorn.conf.py' \
                 --exclude='_dev_data' \
                 --exclude='fixtures' \
                 --exclude='notebooks' \
                 --exclude='.python-version' \
                 --exclude='versions~' \
                 --exclude='_patches~' \
                 --exclude='debug.log' \
                 --exclude='*.orig' \
                 --exclude='*.swp' \
                 --exclude='nave/static' \
                 --exclude='nave/media' \
                 --exclude='*.pid' \
                 --exclude='*.egg-info' \
                 --exclude='.cache' \
                 --exclude='celerybeat-schedule' \
                 --exclude='celerybeat.pid'

# Rsync options
RSYNC_OPTS = -avz --delete $(RSYNC_EXCLUDES)

# Check if SSH_HOST is set
.PHONY: check-ssh-host
check-ssh-host:
ifndef SSH_HOST
	$(error SSH_HOST is not set. Usage: make deploy SSH_HOST=user@server.example.com)
endif

# Deploy to remote server
.PHONY: deploy
deploy: check-ssh-host
	@echo "Deploying to $(SSH_HOST):$(DEPLOY_PATH)"
	@echo "-------------------------------------------"
	rsync $(RSYNC_OPTS) ./ $(SSH_HOST):$(DEPLOY_PATH)/
	@echo "Fixing ownership to $(DEPLOY_USER)..."
	ssh $(SSH_HOST) "chown -R $(DEPLOY_USER):$(DEPLOY_USER) $(DEPLOY_PATH)"
	@echo "-------------------------------------------"
	@echo "Restarting nave service..."
	ssh $(SSH_HOST) "systemctl restart nave"
	@echo "-------------------------------------------"
	@echo "Deployment complete!"

# Dry-run deployment (show what would be transferred)
.PHONY: deploy-dry-run
deploy-dry-run: check-ssh-host
	@echo "DRY RUN - Deploying to $(SSH_HOST):$(DEPLOY_PATH)"
	@echo "-------------------------------------------"
	rsync $(RSYNC_OPTS) --dry-run ./ $(SSH_HOST):$(DEPLOY_PATH)/
	@echo "-------------------------------------------"
	@echo "This was a dry run. No files were transferred."

# Deploy only the project-specific files (nave/projects/$(ORG_ID))
.PHONY: deploy-project
deploy-project: check-ssh-host
	@echo "Deploying project $(ORG_ID) to $(SSH_HOST):$(DEPLOY_PATH)/nave/projects/$(ORG_ID)"
	@echo "-------------------------------------------"
	rsync $(RSYNC_OPTS) ./nave/projects/$(ORG_ID)/ $(SSH_HOST):$(DEPLOY_PATH)/nave/projects/$(ORG_ID)/
	@echo "Fixing ownership to $(DEPLOY_USER)..."
	ssh $(SSH_HOST) "chown -R $(DEPLOY_USER):$(DEPLOY_USER) $(DEPLOY_PATH)/nave/projects/$(ORG_ID)"
	@echo "-------------------------------------------"
	@echo "Restarting nave service..."
	ssh $(SSH_HOST) "systemctl restart nave"
	@echo "-------------------------------------------"
	@echo "Project deployment complete!"

# Fetch remote version to local versions~ folder
.PHONY: fetch-remote
fetch-remote: check-ssh-host
	@echo "Fetching from $(SSH_HOST):$(DEPLOY_PATH) to ./versions~/$(notdir $(DEPLOY_PATH))"
	@mkdir -p ./versions~/$(notdir $(DEPLOY_PATH))
	rsync $(RSYNC_OPTS) $(SSH_HOST):$(DEPLOY_PATH)/ ./versions~/$(notdir $(DEPLOY_PATH))/
	@echo "Fetch complete!"

# Show deployment help
.PHONY: deploy-help
deploy-help:
	@echo "Deployment Commands:"
	@echo "  make deploy SSH_HOST=user@server           - Deploy to remote server"
	@echo "  make deploy-dry-run SSH_HOST=user@server   - Show what would be deployed"
	@echo "  make deploy-project SSH_HOST=user@server   - Deploy only project files"
	@echo "  make fetch-remote SSH_HOST=user@server     - Fetch remote version locally"
	@echo ""
	@echo "Variables:"
	@echo "  SSH_HOST    - Required. SSH destination (e.g., user@server.example.com)"
	@echo "  DEPLOY_PATH - Deploy target path (default: /opt/hub3/$(ORG_ID)/nave_app)"
	@echo "  DEPLOY_USER - User that owns deployed files (default: $(ORG_ID))"
	@echo "  ORG_ID      - Organization/project ID (default: dcn)"
	@echo ""
	@echo "Examples:"
	@echo "  # Deploy to DCN staging:"
	@echo "  make deploy SSH_HOST=deploy@dcn-acpt DEPLOY_PATH=/opt/hub3/dcn/staging/nave_app"
	@echo ""
	@echo "  # Deploy to production:"
	@echo "  make deploy SSH_HOST=deploy@dcn-prod DEPLOY_PATH=/opt/hub3/dcn/nave_app"
	@echo ""
	@echo "  # Deploy only dcn project files:"
	@echo "  make deploy-project SSH_HOST=deploy@dcn-prod ORG_ID=dcn"
