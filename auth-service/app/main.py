import os
import secrets
from datetime import datetime, timedelta, timezone

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Cloud Authentication Service",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/authdb"
)

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "development-secret"
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30

REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============================================================
# SECURITY
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

security = HTTPBearer()


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    return pwd_context.verify(
        password,
        password_hash
    )


# ============================================================
# JWT FUNCTIONS
# ============================================================

def create_access_token(
    user_id: int,
    email: str,
    role: str
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


def create_refresh_token() -> str:

    return secrets.token_urlsafe(64)


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )


# ============================================================
# ADMIN AUTHORIZATION
# ============================================================

def get_current_admin(
    current_user=Depends(get_current_user)
):

    role = current_user.get("role")

    if role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "service": "authentication-service",
        "status": "healthy"
    }


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register(data: RegisterRequest):

    password_hash = hash_password(
        data.password
    )

    try:

        with psycopg.connect(
            DATABASE_URL
        ) as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO users
                    (
                        name,
                        email,
                        password_hash
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        id,
                        name,
                        email,
                        role,
                        created_at
                    """,
                    (
                        data.name,
                        data.email,
                        password_hash
                    )
                )

                user = cursor.fetchone()

                connection.commit()

        return {
            "message": "User registered successfully",
            "user": {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[3],
                "created_at": user[4]
            }
        }

    except psycopg.errors.UniqueViolation:

        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(data: LoginRequest):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    password_hash,
                    role
                FROM users
                WHERE email = %s
                """,
                (data.email,)
            )

            user = cursor.fetchone()

            if not user:

                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )

            if not verify_password(
                data.password,
                user[3]
            ):

                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )

            # Create JWT access token

            access_token = create_access_token(
                user_id=user[0],
                email=user[2],
                role=user[4]
            )

            # Create refresh token

            refresh_token = create_refresh_token()

            refresh_expires_at = (
                datetime.now(timezone.utc)
                + timedelta(
                    days=REFRESH_TOKEN_EXPIRE_DAYS
                )
            )

            cursor.execute(
                """
                INSERT INTO refresh_tokens
                (
                    user_id,
                    token,
                    expires_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user[0],
                    refresh_token,
                    refresh_expires_at
                )
            )

            connection.commit()

    return {

        "message": "Login successful",

        "access_token": access_token,

        "refresh_token": refresh_token,

        "token_type": "bearer",

        "expires_in":
            ACCESS_TOKEN_EXPIRE_MINUTES * 60,

        "refresh_expires_in":
            REFRESH_TOKEN_EXPIRE_DAYS
            * 24
            * 60
            * 60,

        "user": {

            "id": user[0],

            "name": user[1],

            "email": user[2],

            "role": user[4]
        }
    }


# ============================================================
# REFRESH ACCESS TOKEN
# ============================================================

@app.post("/refresh")
def refresh(data: RefreshRequest):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    rt.id,
                    rt.user_id,
                    rt.expires_at,
                    u.email,
                    u.role
                FROM refresh_tokens rt
                JOIN users u
                    ON u.id = rt.user_id
                WHERE rt.token = %s
                """,
                (data.refresh_token,)
            )

            token_record = cursor.fetchone()

            if not token_record:

                raise HTTPException(
                    status_code=401,
                    detail="Invalid refresh token"
                )

            token_id = token_record[0]

            user_id = token_record[1]

            expires_at = token_record[2]

            email = token_record[3]

            role = token_record[4]

            now = datetime.now(
                timezone.utc
            )

            if expires_at.tzinfo is None:

                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            if expires_at <= now:

                cursor.execute(
                    """
                    DELETE FROM refresh_tokens
                    WHERE id = %s
                    """,
                    (token_id,)
                )

                connection.commit()

                raise HTTPException(
                    status_code=401,
                    detail="Refresh token expired"
                )

            access_token = create_access_token(
                user_id=user_id,
                email=email,
                role=role
            )

    return {

        "message":
            "Access token refreshed",

        "access_token":
            access_token,

        "token_type":
            "bearer",

        "expires_in":
            ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/logout")
def logout(data: LogoutRequest):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM refresh_tokens
                WHERE token = %s
                """,
                (data.refresh_token,)
            )

            deleted = cursor.rowcount

            connection.commit()

    if deleted == 0:

        raise HTTPException(
            status_code=404,
            detail="Refresh token not found"
        )

    return {
        "message": "Logout successful"
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/me")
def get_me(
    current_user=Depends(get_current_user)
):

    return {

        "authenticated": True,

        "user": current_user
    }


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.get("/admin")
def admin_dashboard(
    current_admin=Depends(get_current_admin)
):

    return {

        "message":
            "Welcome to the admin dashboard",

        "admin":
            current_admin
    }