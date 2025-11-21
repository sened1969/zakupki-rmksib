import sys
from sqlalchemy import select
from database.connection import SessionLocal
from database.models import User

def create_admin(telegram_id: int, username: str = ""):
    """Создать/обновить пользователя"""
    session = SessionLocal()
    try:
        result = session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalars().first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username or None
            )
            session.add(user)
            print(f"➕ Created new user {telegram_id}")
        else:
            print(f"ℹ️ User {telegram_id} already exists")
        
        session.commit()
        print(f"✅ User {telegram_id} saved!")
    
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    
    finally:
        session.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.create_admin <telegram_id> [username]")
        sys.exit(1)
    
    telegram_id = int(sys.argv[1])
    username = sys.argv[2] if len(sys.argv) > 2 else ""
    
    create_admin(telegram_id, username)

if __name__ == "__main__":
    main()
