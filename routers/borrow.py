from typing import Annotated, List
from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Books, BorrowedBook, User
from datetime import datetime

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

class BorrowedBookResponse(BaseModel):
    id: int
    book_title: str
    user_name: str
    borrowed_date: datetime
    return_date: datetime | None = None

@router.post("/{user_id}/{book_id}")
def borrow_book(user_id: int, book_id: int, db: db_dependency):

    book = db.query(Books).filter(Books.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı!")

    if book.stock <= 0:
        raise HTTPException(status_code=400, detail="Kitap stokta yok!")

    # Kullanıcıyı sorgula
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı!")


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
def return_book(user_id: int, book_id: int, db: db_dependency):
    # Kullanıcının aldığı kitabı bul
    borrowed_book = db.query(BorrowedBook).filter(
        BorrowedBook.user_id == user_id,
        BorrowedBook.book_id == book_id,
        BorrowedBook.return_date == None  # Hala iade edilmemiş kitap
    ).first()

    if not borrowed_book:
        raise HTTPException(status_code=404, detail="İade edilecek kitap bulunamadı!")

    # Kitap stoğunu artır
    book = db.query(Books).filter(Books.id == book_id).first()
    book.stock += 1

    # Kitabı iade olarak işaretle
    borrowed_book.return_date = datetime.now()

    db.commit()
    return {"message": f"'{book.title}' kitabı başarıyla iade edildi."}

@router.get("/borrowed-books", response_model=List[BorrowedBookResponse])
def get_borrowed_books(db: db_dependency):
    borrowed_books = (
        db.query(BorrowedBook)
        .join(User)
        .join(Books)
        .filter(BorrowedBook.return_date.is_(None)) # sadece nullar
        .all()
    )

    if not borrowed_books:
        raise HTTPException(status_code=404, detail="Ödünç alınmış kitap bulunamadı!")

    return [
        BorrowedBookResponse(
            id=borrowed.id,
            book_title=borrowed.book.title,
            user_name=f"{borrowed.user.firstname} {borrowed.user.lastname}",
            borrowed_date=borrowed.borrowed_date,
        )
        for borrowed in borrowed_books
    ]
