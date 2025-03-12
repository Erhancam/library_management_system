from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException,Path
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import User

router= APIRouter(
    prefix="/users",
    tags=["users"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/",status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(User).all()

@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: db_dependency, user_id: int = Path(gt=0)):
    user_model = db.query(User).filter(User.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    db.query(User).filter(User.id == user_id).delete()
    db.commit()


