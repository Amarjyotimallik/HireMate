"""
Script to create a recruiter user for testing.
"""
import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongodb import connect_to_mongodb, close_mongodb_connection, get_users_collection
from app.core.security import hash_password
from app.schemas.user import UserRole
from datetime import datetime

async def create_recruiter():
    await connect_to_mongodb()
    users = get_users_collection()
    
    email = "admin@hiremate.com"
    password = "admin123"
    
    existing = await users.find_one({"email": email})
    if existing:
        print(f"User {email} already exists. Updating password...")
        await users.update_one(
            {"email": email},
            {"$set": {"hashed_password": hash_password(password)}}
        )
        print(f"Updated password for {email} to {password}")
        await close_mongodb_connection()
        return

    user_doc = {
        "email": email,
        "hashed_password": hash_password(password),
        "full_name": "Admin Recruiter",
        "role": UserRole.RECRUITER.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    
    await users.insert_one(user_doc)
    print(f"Created recruiter: {email} / {password}")
    
    await close_mongodb_connection()

if __name__ == "__main__":
    asyncio.run(create_recruiter())
