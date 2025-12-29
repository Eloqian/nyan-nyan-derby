from fastapi import FastAPI
from app.api import auth, players, matches, stages

app = FastAPI(title="Meow Meow Cup API", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(players.router, prefix="/api/v1/players", tags=["Players"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["Matches"])
app.include_router(stages.router, prefix="/api/v1/stages", tags=["Stages"])

@app.get("/")
async def root():
    return {"message": "Welcome to Meow Meow Cup Tournament System"}
