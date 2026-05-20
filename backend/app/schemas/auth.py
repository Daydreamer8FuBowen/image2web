from pydantic import BaseModel


class UserAuthInfo(BaseModel):
    key_name: str
    remaining_count: int
    status: str
    is_admin: bool = False


class AdminAuthInfo(BaseModel):
    is_admin: bool = True
