import json
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from api_models import User, UserCreate, UserUpdate, UserResponse


class UserService:
    def __init__(self, file_path: str = "users.json"):
        self.file_path = Path(file_path)
        self._lock = threading.Lock()

    def _read_users_file(self) -> Dict[str, Any]:
        """Read and parse the users.json file."""
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"users": []}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in users file: {e}")

    def _write_users_file(self, data: Dict[str, Any]) -> None:
        """Write data to the users.json file."""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def _get_next_user_id(self, users: List[Dict[str, Any]]) -> int:
        """Get the next available user ID."""
        if not users:
            return 1
        return max(user["id"] for user in users) + 1

    def get_all_users(self, enabled_only: Optional[bool] = None) -> List[UserResponse]:
        """Get all users, optionally filtered by enabled status."""
        with self._lock:
            data = self._read_users_file()
            users = data.get("users", [])

            if enabled_only is not None:
                users = [u for u in users if u.get("ENABLED", True) == enabled_only]

            return [UserResponse(**user) for user in users]

    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get a specific user by ID."""
        with self._lock:
            data = self._read_users_file()
            users = data.get("users", [])

            for user in users:
                if user["id"] == user_id:
                    return UserResponse(**user)
            return None

    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        with self._lock:
            data = self._read_users_file()
            users = data.get("users", [])

            # Check for duplicate email
            for existing_user in users:
                if existing_user["EMAIL"].lower() == user_data.EMAIL.lower():
                    raise ValueError(f"User with email {user_data.EMAIL} already exists")

            # Generate new ID
            new_id = self._get_next_user_id(users)

            # Create new user dict
            new_user = user_data.dict()
            new_user["id"] = new_id

            # Add to users list
            users.append(new_user)
            data["users"] = users

            # Write back to file
            self._write_users_file(data)

            return UserResponse(**new_user)

    def update_user(self, user_id: int, user_data: UserUpdate, partial: bool = True) -> Optional[UserResponse]:
        """Update an existing user. If partial=False, replace entire user (PUT), if True, partial update (PATCH)."""
        with self._lock:
            data = self._read_users_file()
            users = data.get("users", [])

            # Find user index
            user_index = None
            for i, user in enumerate(users):
                if user["id"] == user_id:
                    user_index = i
                    break

            if user_index is None:
                return None

            existing_user = users[user_index]

            if partial:
                # PATCH: Update only provided fields
                update_dict = user_data.dict(exclude_unset=True)

                # Check for email conflicts (only if email is being updated)
                if "EMAIL" in update_dict:
                    new_email = update_dict["EMAIL"].lower()
                    for i, other_user in enumerate(users):
                        if i != user_index and other_user["EMAIL"].lower() == new_email:
                            raise ValueError(f"User with email {update_dict['EMAIL']} already exists")

                # Update existing user with new values
                for key, value in update_dict.items():
                    existing_user[key] = value
            else:
                # PUT: Replace entire user (except ID)
                update_dict = user_data.dict(exclude_unset=True)

                # Check for email conflicts
                if "EMAIL" in update_dict:
                    new_email = update_dict["EMAIL"].lower()
                    for i, other_user in enumerate(users):
                        if i != user_index and other_user["EMAIL"].lower() == new_email:
                            raise ValueError(f"User with email {update_dict['EMAIL']} already exists")

                # Keep the ID and replace everything else
                updated_user = update_dict.copy()
                updated_user["id"] = user_id

                # Fill in any missing required fields with defaults if not provided
                if "ENABLED" not in updated_user:
                    updated_user["ENABLED"] = True
                if "TIMEZONE" not in updated_user:
                    updated_user["TIMEZONE"] = "America/New_York"
                if "VEHICLE_TYPE" not in updated_user:
                    updated_user["VEHICLE_TYPE"] = "motorcycle"
                if "COMMUTE_DAYS" not in updated_user:
                    updated_user["COMMUTE_DAYS"] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                if "BACKUP_EMAIL" not in updated_user:
                    updated_user["BACKUP_EMAIL"] = None

                users[user_index] = updated_user
                existing_user = updated_user

            # Write back to file
            data["users"] = users
            self._write_users_file(data)

            return UserResponse(**existing_user)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID. Returns True if user was deleted, False if not found."""
        with self._lock:
            data = self._read_users_file()
            users = data.get("users", [])

            # Find and remove user
            for i, user in enumerate(users):
                if user["id"] == user_id:
                    users.pop(i)
                    data["users"] = users
                    self._write_users_file(data)
                    return True

            return False

    def get_user_enabled_status(self, user_id: int) -> Optional[bool]:
        """Get the enabled status of a specific user."""
        user = self.get_user_by_id(user_id)
        return user.ENABLED if user else None

    def update_user_enabled_status(self, user_id: int, enabled: bool) -> Optional[bool]:
        """Update only the enabled status of a user."""
        with self._lock:
            data = self._read_users_file()
            users = data.get("users", [])

            for user in users:
                if user["id"] == user_id:
                    user["ENABLED"] = enabled
                    data["users"] = users
                    self._write_users_file(data)
                    return enabled

            return None

    def user_exists(self, user_id: int) -> bool:
        """Check if a user exists by ID."""
        return self.get_user_by_id(user_id) is not None

    def get_users_count(self, enabled_only: Optional[bool] = None) -> int:
        """Get the total count of users, optionally filtered by enabled status."""
        users = self.get_all_users(enabled_only=enabled_only)
        return len(users)