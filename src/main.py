from fastapi import FastAPI
from src.game import game_router
from src.submission import submit_router
from src.user import user_router


app = FastAPI()

app.include_router(user_router)
app.include_router(game_router)
app.include_router(submit_router)

# demo code routes
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
#
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
