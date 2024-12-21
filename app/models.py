from pydantic import BaseModel
from typing import Optional, List

class UserRegistration(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class LinkID(BaseModel):
    user_email: str
    external_id: str

class Post(BaseModel):
    title: str
    content: str

class UserWithPosts(BaseModel):
    username: str
    email: str
    posts: List[Post]
