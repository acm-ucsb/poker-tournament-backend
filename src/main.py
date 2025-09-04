from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.game import game_router
from src.submission import submit_router
from src.user import user_router
from src.admin import admin_router

import random

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://acm-poker-tournament.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# this is daniel messing around
@app.get("/")
def hello():
    hellos = [
        "hello",
        "hiiiiii",
        "nihao",
        "annyeong",
        "konnichiwa",
        "howdy",
        "chao",
        "chau",
        "ciao",
        "hej",
        "hola",
        "bonjour",
        "._.",
        ":3",
        ":p",
    ]
    return f"{hellos[random.randint(0, len(hellos) - 1)]} from the backend!"


app.include_router(user_router)
app.include_router(game_router)
app.include_router(submit_router)
app.include_router(admin_router)
