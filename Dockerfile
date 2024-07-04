FROM python:3.10-alpine3.20
LABEL maintainer="alertme.tech"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN \
    apk add --no-cache \
    gdal-dev \
    geos-dev \
    gcc \
    musl-dev \
    proj-dev \
    libffi-dev \
    jpeg-dev \
    zlib-dev \
    bash \
    && apk add --no-cache --virtual .build-deps \
    build-base \
    && apk add postgresql-libs && \
    apk add --virtual .build-deps gcc musl-dev postgresql-dev && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user


RUN apk del .build-deps

ENV PATH="/py/bin:$PATH"

USER django-user


