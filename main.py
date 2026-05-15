# main.py - Full working version without bcrypt
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Set
from jose import JWTError, jwt
import hashlib
import uvicorn

app = FastAPI(title="JWT Authentication API")

# Configuration
SECRET_KEY = "your-super-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

# Database
users_db: Dict[str, dict] = {}
blacklisted_tokens: Set[str] = set()

# Models
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# Helper functions
def hash_password(password: str) -> str:
    """Simple password hashing (not as secure as bcrypt but works)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password"""
    return hash_password(plain) == hashed

def create_token(username: str) -> tuple:
    """Create JWT token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token, expire

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from token"""
    token = credentials.credentials
    
    # Check if blacklisted
    if token in blacklisted_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Endpoints
@app.post("/register")
def register(user: UserRegister):
    """Register a new user"""
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    users_db[user.username] = {
        "username": user.username,
        "password": hash_password(user.password),
        "email": user.email,
        "created_at": datetime.now().isoformat()
    }
    
    return {"message": "User registered successfully", "username": user.username}

@app.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    """Login and get access token"""
    if user.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user.password, users_db[user.username]["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token, expire = create_token(user.username)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.post("/logout")
def logout(current_user: str = Depends(get_current_user), 
           credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout - invalidate the token"""
    blacklisted_tokens.add(credentials.credentials)
    return {"message": f"User {current_user} logged out successfully"}

@app.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    """Example protected route"""
    return {
        "message": f"Hello {current_user}! You have access to this protected resource",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/me")
def get_my_info(current_user: str = Depends(get_current_user)):
    """Get current user information"""
    user = users_db.get(current_user)
    return {
        "username": user["username"],
        "email": user.get("email"),
        "created_at": user["created_at"]
    }

@app.get("/")
def root():
    return {
        "api": "JWT Authentication API",
        "version": "1.0",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /login",
            "logout": "POST /logout",
            "protected": "GET /protected",
            "my_info": "GET /me"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Authentication Server...")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔑 Try: POST /register then POST /login")
    uvicorn.run(app, host="0.0.0.0", port=8000)