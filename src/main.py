from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.game import game_router
from src.submission import submit_router
from src.user import user_router
from src.admin import admin_router

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

app.include_router(user_router)
app.include_router(game_router)
app.include_router(submit_router)
app.include_router(admin_router)

# demo code routes
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
#
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
