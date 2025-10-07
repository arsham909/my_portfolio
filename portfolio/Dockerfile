# pull official base image
FROM python:3.11-slim-bullseye

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apt-get update && apt-get install -y netcat

# install dependencies
RUN pip install --upgrade pip
# Step 1: Copy requirements.txt FIRST so pip can install them
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Step 2: Copy ALL required files, including entrypoint.sh and your app code
# This single command copies everything from your host build context (e.g., the directory with Dockerfile)
# into the container's WORKDIR (/usr/src/app).
COPY ./entrypoint.sh  .

# Set permissions and format for entrypoint.sh
# Assuming entrypoint.sh is now at /usr/src/app/portfolio/entrypoint.sh or /usr/src/app/entrypoint.sh
# Based on your original, it seems you want entrypoint.sh at the root of WORKDIR, so you must adjust the path if your final COPY changes its location.

# Let's adjust this to correctly reference where the file lands after 'COPY . .'
# ASSUMPTION: 'entrypoint.sh' is directly in the same folder as the Dockerfile.
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# # pull official base image
# FROM python:3.11-slim-bullseye

# # set work directory
# WORKDIR /usr/src/app

# # set environment variables
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # install system dependencies
# RUN apt-get update && apt-get install -y netcat

# # install dependencies
# RUN pip install --upgrade pip
# COPY ./requirements.txt .
# RUN pip install -r requirements.txt

# # copy entrypoint.sh
# COPY ./portfolio/entrypoint.sh .
# RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
# RUN chmod +x /usr/src/app/entrypoint.sh

# # copy project
# COPY . .

# # run entrypoint.sh
# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]