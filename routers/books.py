from typing import Annotated
from fastapi import Depends, HTTPException, Path, APIRouter
from pydantic import BaseModel ,Field
from sqlalchemy.orm import Session
from starlette import status
import models
from models import Books
from database import engine, SessionLocal
from .auth import get_current_user


router = APIRouter(
    prefix="/books",
    tags=["books"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class BookRequest(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    isbn: str = Field(min_length=3, max_length=100)
    publication_year: int = Field(gt=1900, lt=2025)
    genre: str = Field(min_length=3, max_length=100)
    stock: int = Field(gt=-1)
    author_id: int = Field(gt=-1)

class BookResponse(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    isbn: str = Field(min_length=3, max_length=100)
    publication_year: int = Field(gt=1900, lt=2025)
    genre: str = Field(min_length=3, max_length=100)
    stock: int = Field(gt=-1)
    author_name: str

class Config:
    orm_mode = True


@router.get("/",status_code=status.HTTP_200_OK)
async def read_all( db: db_dependency):


    return db.query(Books).all()


@router.get("/{books_title}", status_code=status.HTTP_200_OK, response_model=BookResponse)
async def read_books(user: user_dependency, db: db_dependency,
                     books_title: str):
    if user is None:
        raise HTTPException(status_code=401, detail='Kullanıcı Bulunamadı')

    books_model = db.query(Books).join(models.Author).filter(Books.title == books_title).first()

    if books_model:

        return BookResponse(
            title=books_model.title,
            isbn=books_model.isbn,
            publication_year=books_model.publication_year,
            genre=books_model.genre,
            stock=books_model.stock,
            author_name=books_model.author.name
        )

    raise HTTPException(status_code=404, detail="Kitap bulunamadı.")


@router.post("/books",status_code=status.HTTP_201_CREATED)
async def create_book(db:db_dependency,
                      book_request: BookRequest):


    book_model = Books(**book_request.model_dump(),)

    db.add(book_model)
    db.commit()

@router.put("/{books_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_book(user: user_dependency,
                      db: db_dependency,
                      book_request: BookRequest,
                      books_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail= 'Kullanıcı Bulunamadı')

    book_model = db.query(Books).filter(Books.id == books_id).first()
    if book_model is None:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı.")

    book_model.title = book_request.title
    book_model.isbn = book_request.isbn
    book_model.publication_year = book_request.publication_year
    book_model.genre = book_request.genre

    db.add(book_model)
    db.commit()

@router.delete("/{books_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(user: user_dependency, db: db_dependency,
                      books_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail= 'Kullanıcı Bulunamadı')

    book_model = db.query(Books).filter(Books.id == books_id).first()
    if book_model is None:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı.")
    db.query(Books).filter(Books.id == books_id).delete()
    db.commit()
