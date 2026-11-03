from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupDetails(BaseModel):
    """What a first-time student tells PCELL so they can verify the request."""

    roll_number: str = Field(min_length=1, max_length=64)
    course: str = Field(min_length=1, max_length=128)
    batch: str = Field(min_length=1, max_length=32)
    phone: str | None = Field(default=None, max_length=32)


class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token from the "Sign in with Google" button
    details: SignupDetails | None = None


class GoogleLoginResponse(BaseModel):
    # OK -> access_token set | DETAILS_REQUIRED -> first visit, ask for details | PENDING -> waiting for PCELL/TPO
    status: str
    message: str | None = None
    email: str | None = None
    full_name: str | None = None
    access_token: str | None = None
    token_type: str = "bearer"
    role: UserRole | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole

    model_config = {"from_attributes": True}
