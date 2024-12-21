import os
from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from pymongo import MongoClient
from app.models import UserRegistration, UserLogin, LinkID, UserWithPosts, Post
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB client setup
MONGO_URI = os.getenv("DATABASE_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

client = MongoClient(MONGO_URI)
print(client)
db = client['user_management_db']
users_collection = db['users']
posts_collection = db['posts']

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# Helper function to hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# Registration endpoint
@router.post("/register")
async def register_user(user: UserRegistration):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hashed_password
    })
    return {"message": "User registered successfully"}

# Login endpoint
@router.post("/login")
async def login_user(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful"}

# Link ID endpoint
@router.post("/link_id")
async def link_user_id(link: LinkID):
    db_user = users_collection.find_one({"email": link.user_email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    users_collection.update_one(
        {"email": link.user_email},
        {"$set": {"external_id": link.external_id}}
    )
    return {"message": f"External ID {link.external_id} linked to user {link.user_email}"}

# Join endpoint to get user with their posts
@router.get("/user_with_posts/{user_email}", response_model=UserWithPosts)
async def get_user_with_posts(user_email: str):
    user = users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = list(posts_collection.find({"user_email": user_email}))
    return {
        "username": user["username"],
        "email": user["email"],
        "posts": [Post(title=post["title"], content=post["content"]) for post in posts]
    }

# Chain delete endpoint to remove a user and their associated data
@router.delete("/delete_user/{user_email}")
async def delete_user(user_email: str):
    db_user = users_collection.find_one({"email": user_email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete posts associated with the user
    posts_collection.delete_many({"user_email": user_email})
    
    # Delete the user record
    users_collection.delete_one({"email": user_email})
    
    return {"message": f"User {user_email} and associated data deleted"}
