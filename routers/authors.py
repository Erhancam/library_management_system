from http.client import HTTPException
from fastapi import APIRouter, Depends, Path
from typing import Annotated, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
import models
from database import SessionLocal
from models import Author

router = APIRouter(
    prefix="/authors",
    tags=["authors"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

class BookResponse(BaseModel):
    id: int
    title: str
    isbn: str
    publication_year: int
    genre: str
    stock: int
    author_id: int

class AuthorBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)

class AuthorWithBooksResponse(BaseModel):
    name: str
    books: List[BookResponse]



@router.get("/",status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Author).all()


@router.get("/{authors_name}", response_model=AuthorWithBooksResponse)
async def read_authors(db: db_dependency, authors_name: str):
    author = db.query(Author).join(models.Books).filter(Author.name == authors_name).first()

    if author:
        return AuthorWithBooksResponse(
            name=author.name,
            books=[BookResponse(
                id=books.id,
                title=books.title,
                isbn=books.isbn,
                publication_year=books.publication_year,
                genre=books.genre,
                stock=books.stock,
                author_id=books.author_id
            ) for books in author.books]
    )
    raise HTTPException(status_code=404, detail="Yazar bulunamadı.")

@router.post("/authors",status_code=status.HTTP_201_CREATED)
async def create_author(db:db_dependency, author_request: AuthorBase):
    author_model = Author(**author_request.model_dump())

    db.add(author_model)
    db.commit()

@router.delete("/{authors_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(db: db_dependency, authors_id: int = Path(gt=0)):
    author_model = db.query(Author).filter(Author.id == authors_id).first()
    if author_model is None:
        raise HTTPException(status_code=404, detail="Yazar bulunamadı.")
    db.query(Author).filter(Author.id == authors_id).delete()
    db.commit()
