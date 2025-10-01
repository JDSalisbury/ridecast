from pydantic import BaseModel, Field, validator
from typing import Dict, List, Tuple, Optional


class LocationCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90,
                            description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180,
                             description="Longitude coordinate")

    def to_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float]) -> 'LocationCoordinates':
        return cls(latitude=coords[0], longitude=coords[1])


class WeatherPreferences(BaseModel):
    max_rain_chance: int = Field(..., ge=0, le=100,
                                 description="Maximum acceptable rain chance percentage")
    min_temp_f: int = Field(...,
                            description="Minimum acceptable temperature in Fahrenheit")
    max_wind_mph: int = Field(..., ge=0,
                              description="Maximum acceptable wind speed in mph")
    preferred_conditions: List[str] = Field(
        ..., description="List of preferred weather conditions")


class NotificationSettings(BaseModel):
    send_morning_only: bool = Field(
        default=False, description="Whether to send only morning notifications")
    send_if_no_ride: bool = Field(
        default=True, description="Whether to send notification when not riding")
    advance_notice_hours: int = Field(
        default=1, ge=0, le=24, description="Hours of advance notice")


class RideHours(BaseModel):
    start_hour: int = Field(..., ge=0, le=23,
                            description="Start hour in 24-hour format")
    end_hour: int = Field(..., ge=0, le=23,
                          description="End hour in 24-hour format")

    def to_tuple(self) -> Tuple[int, int]:
        return (self.start_hour, self.end_hour)

    @classmethod
    def from_tuple(cls, hours: Tuple[int, int]) -> 'RideHours':
        return cls(start_hour=hours[0], end_hour=hours[1])

    @validator('end_hour')
    def end_after_start(cls, v, values):
        if 'start_hour' in values and v <= values['start_hour']:
            raise ValueError('End hour must be after start hour')
        return v


class User(BaseModel):
    id: int = Field(..., gt=0, description="Unique user identifier")
    NAME: str = Field(..., min_length=1, description="Full name of the user")
    EMAIL: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$',
                       description="Valid email address")
    ENABLED: bool = Field(
        default=True, description="Whether the user account is enabled")
    TIMEZONE: str = Field(default="America/New_York",
                          description="User's timezone")
    RIDE_IN_HOURS: str = Field(..., pattern=r'^\(\d{1,2},\d{1,2}\)$',
                               description="Riding in hours as tuple string")
    RIDE_BACK_HOURS: str = Field(
        ..., pattern=r'^\(\d{1,2},\d{1,2}\)$', description="Riding back hours as tuple string")
    LOCATIONS: Dict[str, str] = Field(
        ..., description="Location name to coordinate string mapping")
    WEATHER_PREFERENCES: WeatherPreferences
    NOTIFICATION_SETTINGS: NotificationSettings
    VEHICLE_TYPE: str = Field(default="motorcycle",
                              description="Type of vehicle")
    COMMUTE_DAYS: List[str] = Field(default=["Monday", "Tuesday", "Wednesday",
                                    "Thursday", "Friday"], description="Days of the week for commuting")
    BACKUP_EMAIL: Optional[str] = Field(
        default=None, description="Backup email address")
    DISPLAY_NAME: str = Field(..., min_length=1,
                              description="Display name for the user")

    @validator('COMMUTE_DAYS')
    def validate_commute_days(cls, v):
        valid_days = ["Monday", "Tuesday", "Wednesday",
                      "Thursday", "Friday", "Saturday", "Sunday"]
        for day in v:
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}")
        return v

    @validator('BACKUP_EMAIL')
    def validate_backup_email(cls, v):
        if v is not None and not v.strip():
            return None
        if v is not None and not v.count('@') == 1:
            raise ValueError('Invalid backup email format')
        return v


class UserCreate(BaseModel):
    NAME: str = Field(..., min_length=1, description="Full name of the user")
    EMAIL: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$',
                       description="Valid email address")
    ENABLED: bool = Field(
        default=True, description="Whether the user account is enabled")
    TIMEZONE: str = Field(default="America/New_York",
                          description="User's timezone")
    RIDE_IN_HOURS: str = Field(..., pattern=r'^\(\d{1,2},\d{1,2}\)$',
                               description="Riding in hours as tuple string")
    RIDE_BACK_HOURS: str = Field(
        ..., pattern=r'^\(\d{1,2},\d{1,2}\)$', description="Riding back hours as tuple string")
    LOCATIONS: Dict[str, str] = Field(
        ..., description="Location name to coordinate string mapping")
    WEATHER_PREFERENCES: WeatherPreferences
    NOTIFICATION_SETTINGS: NotificationSettings
    VEHICLE_TYPE: str = Field(default="motorcycle",
                              description="Type of vehicle")
    COMMUTE_DAYS: List[str] = Field(default=["Monday", "Tuesday", "Wednesday",
                                    "Thursday", "Friday"], description="Days of the week for commuting")
    BACKUP_EMAIL: Optional[str] = Field(
        default=None, description="Backup email address")
    DISPLAY_NAME: str = Field(..., min_length=1,
                              description="Display name for the user")


class UserUpdate(BaseModel):
    NAME: Optional[str] = Field(
        None, min_length=1, description="Full name of the user")
    EMAIL: Optional[str] = Field(
        None, pattern=r'^[^@]+@[^@]+\.[^@]+$', description="Valid email address")
    ENABLED: Optional[bool] = Field(
        None, description="Whether the user account is enabled")
    TIMEZONE: Optional[str] = Field(None, description="User's timezone")
    RIDE_IN_HOURS: Optional[str] = Field(
        None, pattern=r'^\(\d{1,2},\d{1,2}\)$', description="Riding in hours as tuple string")
    RIDE_BACK_HOURS: Optional[str] = Field(
        None, pattern=r'^\(\d{1,2},\d{1,2}\)$', description="Riding back hours as tuple string")
    LOCATIONS: Optional[Dict[str, str]] = Field(
        None, description="Location name to coordinate string mapping")
    WEATHER_PREFERENCES: Optional[WeatherPreferences] = None
    NOTIFICATION_SETTINGS: Optional[NotificationSettings] = None
    VEHICLE_TYPE: Optional[str] = Field(None, description="Type of vehicle")
    COMMUTE_DAYS: Optional[List[str]] = Field(
        None, description="Days of the week for commuting")
    BACKUP_EMAIL: Optional[str] = Field(
        None, description="Backup email address")
    DISPLAY_NAME: Optional[str] = Field(
        None, min_length=1, description="Display name for the user")


class UserResponse(BaseModel):
    id: int
    NAME: str
    EMAIL: str
    ENABLED: bool
    TIMEZONE: str
    RIDE_IN_HOURS: str
    RIDE_BACK_HOURS: str
    LOCATIONS: Dict[str, str]
    WEATHER_PREFERENCES: WeatherPreferences
    NOTIFICATION_SETTINGS: NotificationSettings
    VEHICLE_TYPE: str
    COMMUTE_DAYS: List[str]
    BACKUP_EMAIL: Optional[str]
    DISPLAY_NAME: str


class UsersListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class EnabledStatusResponse(BaseModel):
    user_id: int
    enabled: bool
