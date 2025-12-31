
from sqlmodel import select
from app.db import get_session
from app.models.user import User
from app.core.security import get_password_hash
import os

async def create_default_admin():
    async for session in get_session():
        try:
            # Check if any admin exists
            statement = select(User).where(User.is_admin == True)
            result = await session.exec(statement)
            admin_user = result.first()
            
            if not admin_user:
                print("No admin user found. Creating default admin...")
                default_admin = User(
                    username=os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
                    hashed_password=get_password_hash(os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")),
                    is_admin=True,
                    email="admin@example.com"
                )
                session.add(default_admin)
                await session.commit()
                print("Default admin created successfully.")
            else:
                print("Admin user already exists. Skipping creation.")
        except Exception as e:
            print(f"Warning: Could not create default admin. Database might not be ready. Error: {e}")
        
        # Since get_session yields, we break after using the session once
        break
