# Dockerfile
FROM python:3.6-slim

# Set work directory
WORKDIR /app

# Install any system dependencies (adjust if you need other packages)
RUN apt-get update && \
  apt-get install -y \
  build-essential \
  libpq-dev \
  libgeos-dev \
  zlib1g-dev \
  libjpeg-dev \
  libtiff-dev \
  libfreetype6-dev \
  libxml2-dev \
  libxslt-dev \
  liblcms2-dev && \
  rm -rf /var/lib/apt/lists/*


# Create a virtual environment inside the container
RUN python -m venv /opt/venv

# Install Django and other dependencies into the virtual environment
COPY requirements/base.txt .
COPY requirements/library_base.txt .
RUN /opt/venv/bin/pip install -r base.txt

# Set the PATH to use the virtual environment by default
ENV PATH="/opt/venv/bin:$PATH"

# Ensure manage.py commands run properly
CMD ["python", "manage.py"]

