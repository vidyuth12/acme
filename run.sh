#!/bin/bash

echo "Starting Acme Product Importer..."

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Building and starting Docker containers..."
docker-compose up --build
