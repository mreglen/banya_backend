from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  
from app.database import Base, engine
from app.routers import api_router
from fastapi.middleware.cors import CORSMiddleware
import os


Base.metadata.create_all(bind=engine)

app = FastAPI(title='Бани')


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*' ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.mount("/img", StaticFiles(directory="public/img"), name="static_images")

app.include_router(api_router)