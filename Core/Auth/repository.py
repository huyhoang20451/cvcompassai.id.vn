from sqlmodel import Session, select
from models import User_db

def get_user_by_username(session: Session, username: str) -> User_db:
    statement = select(User_db).where(User_db.username == username)
    return session.exec(statement).first()

def save_user_to_db(session: Session, user: User_db) -> User_db:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user