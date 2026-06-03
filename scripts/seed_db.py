import asyncio
import sys
import os

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.schema import User, Monitor

async def seed():
    async with AsyncSessionLocal() as db:
        # Create a dummy user
        user = User(email="admin@monitor.local", password_hash="fakehash")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create a monitor for Google
        monitor1 = Monitor(
            user_id=user.id,
            name="Google Search",
            url="https://www.google.com",
            interval_seconds=10,
        )
        # Create a monitor for a fake failing URL
        monitor2 = Monitor(
            user_id=user.id,
            name="Fake API (Should Fail)",
            url="https://this-website-does-not-exist.local",
            interval_seconds=10,
        )
        
        db.add_all([monitor1, monitor2])
        await db.commit()
        
        print("Database seeded with 1 User and 2 Monitors!")

if __name__ == "__main__":
    asyncio.run(seed())