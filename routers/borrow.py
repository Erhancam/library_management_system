from typing import Annotated, List
from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Books, BorrowedBook, User
from datetime import datetime
from .auth import get_current_user
router = APIRouter(
    prefix="/borrow",
    tags=["borrow"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class BorrowedBookResponse(BaseModel):
    id: int
    book_title: str
    user_name: str
    borrowed_date: datetime
    return_date: datetime | None = None

@router.post("/{user_id}/{book_id}")
def borrow_book(user:user_dependency ,user_id: int, book_id: int, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Kullanıcı Bulunamadı')

    book = db.query(Books).filter(Books.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı.")

    if book.stock <= 0:
        raise HTTPException(status_code=400, detail="Kitap stokta yok.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")


    borrowed_book = BorrowedBook(
        user_id=user_id,
        book_id=book_id,
        borrowed_date=datetime.now()
    )
    db.add(borrowed_book)

    book.stock -= 1

    db.commit()
    return {"message": f"'{book.title}' kitabı {user.username} tarafından ödünç alındı."}

@router.post("/return/{user_id}/{book_id}")
def return_book(user:user_dependency , user_id: int,
                book_id: int, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Kullanıcı Bulunamadı')

    borrowed_book = db.query(BorrowedBook).filter(
        BorrowedBook.user_id == user_id,
        BorrowedBook.book_id == book_id,
        BorrowedBook.return_date == None
    ).first()

    if not borrowed_book:
        raise HTTPException(status_code=404, detail="İade edilecek kitap bulunamadı.")

    book = db.query(Books).filter(Books.id == book_id).first()
    book.stock += 1

    borrowed_book.return_date = datetime.now()

    db.commit()
    return {"message": f"'{book.title}' kitabı başarıyla iade edildi."}

@router.get("/borrowed-books", response_model=List[BorrowedBookResponse])
def get_borrowed_books(user:user_dependency ,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Kullanıcı Bulunamadı')

    borrowed_books = (
        db.query(BorrowedBook)
        .join(User)
        .join(Books)
        .filter(BorrowedBook.return_date.is_(None)) # sadece nullar
        .all()
    )

    if not borrowed_books:
        raise HTTPException(status_code=404, detail="Ödünç alınmış kitap bulunamadı.")

    return [
        BorrowedBookResponse(
            id=borrowed.id,
            book_title=borrowed.book.title,
            user_name=f"{borrowed.user.firstname} {borrowed.user.lastname}",
            borrowed_date=borrowed.borrowed_date,
        )
        for borrowed in borrowed_books
    ]


@router.get("/user/{user_id}/history", response_model=List[BorrowedBookResponse])
def get_user_borrow_history(user:user_dependency ,user_id: int, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Kullanıcı Bulunamadı')

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    borrow_history = db.query(BorrowedBook).filter(BorrowedBook.user_id == user_id).all()

    if not borrow_history:
        raise HTTPException(status_code=404, detail="Kullanıcının geçmişinde ödünç aldığı kitap bulunamadı.")

    return [
        BorrowedBookResponse(
            id=borrow.id,
            book_title=borrow.book.title,
            user_name=f"{borrow.user.firstname} {borrow.user.lastname}",
            borrowed_date=borrow.borrowed_date,
            return_date=borrow.return_date
        )
        for borrow in borrow_history
    ]
