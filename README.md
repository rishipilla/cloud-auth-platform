# Cloud Authentication & Authorization Platform

A production-style authentication and authorization platform built with **FastAPI, PostgreSQL, JWT, React, and Docker**.

The project demonstrates how a modern web application can securely handle user identity, authentication, session management, and role-based access control.

## Architecture

```text
                    ┌─────────────────────┐
                    │    React Frontend   │
                    │   Login / Register   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Service   │
                    │                     │
                    │  Register / Login   │
                    │  JWT Authentication │
                    │  Refresh Tokens     │
                    │  RBAC Authorization │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │                     │
                    │       Users         │
                    │   Refresh Tokens    │
                    └─────────────────────┘
```

## Features

- User registration and login
- Secure bcrypt password hashing
- JWT access-token authentication
- Refresh-token based session renewal
- Logout and refresh-token revocation
- Role-based access control
- Protected user profile endpoint
- Protected admin endpoint
- PostgreSQL persistence
- Dockerized backend and database
- React authentication interface
- CORS configuration for frontend integration
- FastAPI automatic API documentation

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Database | PostgreSQL 17 |
| Authentication | JWT |
| Password Security | bcrypt |
| Containers | Docker + Docker Compose |
| API Docs | Swagger / OpenAPI |

## Project Structure

```text
cloud-auth-platform/
├── auth-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py
├── database/
│   └── init.sql
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Authentication Flow

### Registration

1. User submits name, email, and password.
2. Backend validates the request.
3. Password is hashed with bcrypt.
4. User record is stored in PostgreSQL.
5. A successful registration response is returned.

### Login

1. User submits email and password.
2. Backend retrieves the user.
3. Password hash is verified.
4. A short-lived JWT access token is generated.
5. A secure random refresh token is stored in PostgreSQL.
6. Both tokens are returned to the client.

### Accessing Protected Resources

The client sends the access token using:

```http
Authorization: Bearer <access_token>
```

The backend validates the JWT and extracts the user's identity and role.

### Refreshing a Session

When an access token expires, the client can submit its refresh token to:

```http
POST /refresh
```

The backend validates the refresh token and issues a new access token.

### Logout

Logout removes the refresh token from PostgreSQL, preventing it from being used to obtain another access token.

## Role-Based Access Control

Users have a role stored in PostgreSQL.

Default role:

```text
user
```

Administrative users can access protected admin resources:

```http
GET /admin
```

A normal user receives:

```text
403 Forbidden
```

This demonstrates server-side authorization rather than relying only on frontend controls.

## API Endpoints

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | /health | Health check | Public |
| POST | /register | Create account | Public |
| POST | /login | Authenticate user | Public |
| POST | /refresh | Refresh access token | Refresh token |
| POST | /logout | Revoke refresh token | Refresh token |
| GET | /me | Get authenticated user | JWT |
| GET | /admin | Admin-only resource | JWT + Admin |

## Running Locally

### Prerequisites

- Docker Desktop
- Node.js
- npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/rishipilla/cloud-auth-platform.git
cd cloud-auth-platform
```

### 2. Configure environment variables

Create a `.env` file from the example:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/authdb
JWT_SECRET=replace-with-a-real-secret
```

For the Docker Compose setup, the authentication service uses the internal PostgreSQL hostname automatically.

**Never commit `.env` or real secrets to GitHub.**

### 3. Start the backend and database

```bash
docker compose up --build
```

The authentication API will be available at:

```text
http://localhost:8011
```

Swagger documentation:

```text
http://localhost:8011/docs
```

PostgreSQL is exposed locally on port `5433`.

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Security Considerations

This project demonstrates several important authentication practices:

- Passwords are never stored in plaintext.
- Passwords are hashed using bcrypt.
- Access tokens are short-lived.
- Refresh tokens are stored server-side for revocation.
- JWT payloads contain user identity and role information.
- Protected endpoints validate authentication on the server.
- Administrative endpoints enforce role-based authorization.
- Environment secrets are excluded from Git using `.gitignore`.

For production deployment, additional controls such as HTTPS, secure HttpOnly cookies, CSRF protection where applicable, rate limiting, token rotation, audit logging, secret management, and stronger session policies should be considered.

## Example Responses

### Health Check

```json
{
  "service": "authentication-service",
  "status": "healthy"
}
```

### Successful Login

```json
{
  "message": "Login successful",
  "access_token": "<jwt>",
  "refresh_token": "<refresh-token>",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Example User",
    "email": "user@example.com",
    "role": "user"
  }
}
```

Tokens are intentionally represented as placeholders.

## Learning Outcomes

This project demonstrates practical experience with:

- Authentication architecture
- JWT-based security
- Password hashing
- Refresh-token sessions
- Role-based authorization
- REST API development
- PostgreSQL database design
- Docker containerization
- React frontend integration
- API security fundamentals
- Environment and secret management

## Future Improvements

Potential production extensions include:

- Email verification
- Password reset workflow
- OAuth2 / social login
- MFA / TOTP authentication
- Refresh-token rotation
- Redis-based session and rate-limit management
- API Gateway integration
- Audit logging
- HTTPS deployment
- CI/CD pipeline
- Cloud deployment

## License

This project is intended as a portfolio and learning project.
