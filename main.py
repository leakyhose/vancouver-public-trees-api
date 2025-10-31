from fastapi import FastAPI
from api import health, search, trees, species

app = FastAPI()

# search must be included before trees (route ordering)
app.include_router(health.router)
app.include_router(search.router)
app.include_router(trees.router)
app.include_router(species.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
