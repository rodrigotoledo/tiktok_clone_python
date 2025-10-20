# Python Backend Project

A backend service built with Python, using Docker Compose for easy deployment and development.

## Requirements

- Docker
- Docker Compose

## Quick Start

1. Clone the repository

2. Start the application:

```bash
# Start (detached)
docker compose up --build

# Stop and remove containers/networks
docker compose down


docker compose exec backend python reset_db.py
```

## Development

The application runs in a Docker container, making it easy to maintain consistency across different development environments.

### Main Components

- Python FastAPI backend service
- PostgreSQL database
- Docker Compose for container orchestration

## API Documentation

Once the application is running, you can access the API documentation at:
`http://localhost:8000` and database `http://localhost:8080`
