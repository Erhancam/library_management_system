from fastapi import FastAPI
from routers import auth, books, authors, borrow,users,api
import models
from database import engine
app= FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(books.router)

app.include_router(authors.router)

app.include_router(borrow.router)
app.include_router(users.router)
app.include_router(api.router)