
import random
from typing import Annotated
from fastapi import Depends, requests, APIRouter

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Author, Books
import requests

router = APIRouter()
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session, Depends(get_db)]


GENRES = ["fiction", "history", "science", "technology", "fantasy", "mystery", "biography", "self-help"]


def fetch_books_from_google(genre, max_results=100):

    books = []
    for start_index in range(0, max_results, 40):
        params = {
            "q": f"subject:{genre}",
            "startIndex": start_index,
            "maxResults": 40,
            "printType": "books",
            "orderBy": "relevance",
            "langRestrict": "tr"
        }
        response = requests.get(GOOGLE_BOOKS_API, params=params)
        if response.status_code == 200:
            books.extend(response.json().get("items", []))
    return books


@router.post("/generate_books/")
def generate_books(db: db_dependency):
    for year in range(2015, 2025):
        all_books = []

        for genre in GENRES:
            books_data = fetch_books_from_google(genre, max_results=40)
            all_books.extend(books_data)


        books_added = 0
        for item in all_books:
            if books_added >= 100:
                break

            volume_info = item.get("volumeInfo", {})
            title = volume_info.get("title", "Unknown Title")
            isbn_list = volume_info.get("industryIdentifiers", [])
            isbn = isbn_list[0]["identifier"] if isbn_list else str(random.randint(1000000000000, 9999999999999))
            authors = volume_info.get("authors", ["Unknown Author"])
            genre = volume_info.get("categories", ["General"])[0]


            existing_author = db.query(Author).filter(Author.name == authors[0]).first()
            if not existing_author:
                new_author = Author(name=authors[0])
                db.add(new_author)
                db.commit()
                existing_author = new_author

            new_book = Books(
                title=title,
                isbn=isbn,
                publication_year=year,
                genre=genre,
                stock=random.randint(1, 20),
                author_id=existing_author.id
            )
            db.add(new_book)
            books_added += 1

        db.commit()

    return {"message": "1000 kitap başarıyla eklendi!"}
@router.delete("/delete_all")
def delete_all(db: db_dependency):
    db.query(Books).delete()
    db.query(Author).delete()
    db.commit()
    return {"message": "Tüm kitaplar ve yazarlar silindi!"}