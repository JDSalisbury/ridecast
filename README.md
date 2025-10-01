# RideCast

RideCast is a user management API built with FastAPI for managing users and their preferences.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ridecast
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the FastAPI Server

Start the server with:
```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

You can also run it directly with uvicorn:
```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once the server is running, you can access:
- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## Bruno API Collection

This project includes a Bruno API collection for testing the API endpoints.

### What is Bruno?

[Bruno](https://www.usebruno.com/) is a fast and git-friendly open-source API client, similar to Postman or Insomnia.

### Installing Bruno

Download and install Bruno from: https://www.usebruno.com/downloads

### Importing the Collection

1. Open Bruno
2. Click "Open Collection"
3. Navigate to the `bruno-collection` folder in this project
4. Select the folder to import all the API requests

The collection includes requests for:
- Creating users
- Retrieving users (all, by ID, with filters)
- Updating users (full replace with PUT, partial with PATCH)
- Deleting users
- Managing user enabled status
- Health check endpoint

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/users` | List all users (with optional filters) |
| GET | `/users/{user_id}` | Get user by ID |
| POST | `/users` | Create new user |
| PUT | `/users/{user_id}` | Replace user completely |
| PATCH | `/users/{user_id}` | Update user partially |
| DELETE | `/users/{user_id}` | Delete user |
| GET | `/users/{user_id}/enabled` | Get user enabled status |
| PATCH | `/users/{user_id}/enabled` | Update user enabled status |
| GET | `/health` | Health check |

## Project Structure

- `api_server.py` - FastAPI application and endpoints
- `api_models.py` - Pydantic models for API requests/responses
- `user_service.py` - User management service layer
- `models.py` - Core data models
- `bruno-collection/` - Bruno API collection for testing
