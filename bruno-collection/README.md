# RideCast API Bruno Collection

This Bruno collection contains all the API endpoints for the RideCast User Management API.

## Setup

1. Install [Bruno](https://www.usebruno.com/) if you haven't already
2. Open Bruno and import this collection by selecting the `bruno-collection` folder
3. Make sure your FastAPI server is running:
   ```bash
   source venv/bin/activate
   python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
   ```

## Environment

The collection includes a `Local` environment with:
- `baseUrl`: http://localhost:8000

## Available Requests

1. **API Info** - Get basic API information
2. **Health Check** - Check system health and user counts
3. **Get All Users** - Retrieve all users with optional filtering
4. **Get User by ID** - Get a specific user
5. **Create User** - Create a new user
6. **Update User (PUT)** - Replace entire user record
7. **Update User (PATCH)** - Partial user update
8. **Delete User** - Remove a user
9. **Get User Enabled Status** - Check if user is enabled
10. **Update User Enabled Status** - Enable/disable a user

## Usage Tips

- Each request includes documentation with parameter descriptions
- Sample JSON payloads are provided for POST/PUT/PATCH requests
- Query parameters are pre-configured but commented out (use `~` prefix to disable)
- Update the user IDs in the URLs as needed for your testing
- The `Create User` request has a complete example payload you can modify

## API Documentation

You can also view the auto-generated API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc