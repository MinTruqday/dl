from pydantic import BaseModel, Field


class AccountLookup(BaseModel):
    user_ids: list[str] = Field(max_length=5000)
