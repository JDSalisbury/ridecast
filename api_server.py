from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import uvicorn
from api_models import (
    User, UserCreate, UserUpdate, UserResponse,
    UsersListResponse, EnabledStatusResponse
)
from user_service import UserService

app = FastAPI(
    title="RideCast User Management API",
    description="CRUD API for managing RideCast users",
    version="1.0.0"
)

# Initialize user service
user_service = UserService()


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RideCast User Management API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/users", response_model=UsersListResponse)
async def get_users(
    enabled: Optional[bool] = Query(
        None, description="Filter by enabled status"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of users to return")
):
    """Get all users with optional filtering and pagination."""
    try:
        all_users = user_service.get_all_users(enabled_only=enabled)
        total = len(all_users)

        # Apply pagination
        users = all_users[skip:skip + limit]

        return UsersListResponse(users=users, total=total)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving users: {str(e)}")


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a specific user by ID."""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail=f"User with ID {user_id} not found")
    return user


@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate):
    """Create a new user."""
    try:
        return user_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating user: {str(e)}")


@app.put("/users/{user_id}", response_model=UserResponse)
async def replace_user(user_id: int, user_data: UserUpdate):
    """Replace a user entirely (PUT operation)."""
    try:
        # Check if user exists
        if not user_service.user_exists(user_id):
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found")

        updated_user = user_service.update_user(
            user_id, user_data, partial=False)
        if not updated_user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found")

        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating user: {str(e)}")


@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate):
    """Partially update a user (PATCH operation)."""
    try:
        updated_user = user_service.update_user(
            user_id, user_data, partial=True)
        if not updated_user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found")

        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating user: {str(e)}")


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user by ID."""
    try:
        if user_service.delete_user(user_id):
            return {"message": f"User with ID {user_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting user: {str(e)}")


@app.get("/users/{user_id}/enabled", response_model=EnabledStatusResponse)
async def get_user_enabled_status(user_id: int):
    """Get the enabled status of a specific user."""
    enabled_status = user_service.get_user_enabled_status(user_id)
    if enabled_status is None:
        raise HTTPException(
            status_code=404, detail=f"User with ID {user_id} not found")

    return EnabledStatusResponse(user_id=user_id, enabled=enabled_status)


@app.patch("/users/{user_id}/enabled", response_model=EnabledStatusResponse)
async def update_user_enabled_status(user_id: int, enabled_data: dict):
    """Update only the enabled status of a user."""
    try:
        if "enabled" not in enabled_data:
            raise HTTPException(
                status_code=400, detail="Field 'enabled' is required")

        enabled = enabled_data["enabled"]
        if not isinstance(enabled, bool):
            raise HTTPException(
                status_code=400, detail="Field 'enabled' must be a boolean")

        updated_status = user_service.update_user_enabled_status(
            user_id, enabled)
        if updated_status is None:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found")

        return EnabledStatusResponse(user_id=user_id, enabled=updated_status)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating user enabled status: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        total_users = user_service.get_users_count()
        enabled_users = user_service.get_users_count(enabled_only=True)

        return {
            "status": "healthy",
            "users_total": total_users,
            "users_enabled": enabled_users,
            "users_disabled": total_users - enabled_users
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
