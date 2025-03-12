from sqlalchemy import Integer, Column, ForeignKey, String, TIMESTAMP
from sqlalchemy.orm import relationship

from database import Base


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    books = relationship("Books", back_populates="author", lazy= "joined")


class Books(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    isbn = Column(String)
    publication_year = Column(Integer)
    genre = Column(String)
    stock = Column(Integer)
    author_id = Column(Integer, ForeignKey('authors.id'))

    author = relationship("Author", back_populates="books")
    borrowed_books = relationship("BorrowedBook", back_populates="book")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True, nullable=False)
    firstname = Column(String)
    lastname = Column(String)
    hashed_password = Column(String)
    role = Column(String)

    borrowed_books = relationship("BorrowedBook", back_populates="user")


class BorrowedBook(Base):
    __tablename__ = 'borrowed_books'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    borrowed_date = Column(TIMESTAMP, default='CURRENT_TIMESTAMP')
    return_date = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="borrowed_books")
    book = relationship("Books", back_populates="borrowed_books")



