from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, players, matches, stages, tournaments

app = FastAPI(title="Meow Meow Cup API", version="1.0.0")

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:80",
    # Add your production domain here later
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(players.router, prefix="/api/v1/players", tags=["Players"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["Matches"])
app.include_router(stages.router, prefix="/api/v1/stages", tags=["Stages"])
app.include_router(tournaments.router, prefix="/api/v1/tournaments", tags=["Tournaments"])

@app.on_event("startup")
async def on_startup():
    from app.core.create_admin import create_default_admin
    await create_default_admin()

@app.get("/")
async def root():
    return {"message": "Welcome to Meow Meow Cup Tournament System"}
