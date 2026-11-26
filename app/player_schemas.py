from pydantic import BaseModel, Field, field_validator

from app.player_avatars import normalize_avatar


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    avatar: str | None = None

    @field_validator("avatar")
    @classmethod
    def normalize_avatar_value(cls, value: str | None) -> str | None:
        return normalize_avatar(value)


class PlayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    avatar: str | None = None

    @field_validator("avatar")
    @classmethod
    def normalize_avatar_value(cls, value: str | None) -> str | None:
        return normalize_avatar(value)
