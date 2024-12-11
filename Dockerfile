FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV POETRY_VIRTUALENVS_CREATE="false"

RUN mkdir /app
WORKDIR /app

EXPOSE 8000

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./pyproject.toml /app
ADD . /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip  \
    && pip --no-cache-dir install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

ENTRYPOINT ["bash", "/app/entrypoint.sh"]
