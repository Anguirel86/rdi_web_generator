###################
# Builder container
###################
# Build and install dependencies for the webapp
FROM python:3.12.11-alpine3.22 as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy over the Flips code, install dependencies, and build it
COPY ./submodules/Flips ./Flips
RUN apk update && apk add build-base

# Install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# The randomizer needs to be installed as a pip package
# It also needs gcc, so run it after the apk installs
COPY ./submodules/ctrando ./ctrando
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels ctrando/

WORKDIR /usr/src/app/Flips
ENV TARGET="cli"
RUN ./make-linux.sh --profile=no

#################
# Final container
#################
FROM python:3.12.11-alpine3.22

# Set up a user for the webapp
RUN mkdir -p /home/rdi
run addgroup -S rdi && adduser -S rdi -G rdi
ENV HOME=/home/rdi
ENV APP_HOME=/home/rdi/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# Flips needs libstdc++
RUN apk update && apk add libstdc++

# Copy/install dependencies from the builder container
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/Flips/flips /usr/local/bin
RUN pip install --no-cache /wheels/*

#  Copy the webapp files over to the container
COPY ./rdi_webgen .

RUN chown -R rdi:rdi $APP_HOME

# NOTE: bash isn't really needed for normal usage, but is useful for debugging
RUN apk update && apk add bash

# Switch to the webapp user
USER rdi
