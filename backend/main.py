from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

app = FastAPI(title="NBA Game Recaps API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Game(BaseModel):
    id: str
    awayTeam: str
    homeTeam: str
    awayScore: Optional[int] = None
    homeScore: Optional[int] = None
    date: str
    status: str  # "scheduled", "in_progress", "finished"

class GameSummary(BaseModel):
    gameId: str
    summary: str
    generatedAt: str

# Mock data for today's games
def get_todays_games() -> List[Game]:
    """Returns mock data for today's NBA games"""
    today = datetime.now().strftime("%B %d, %Y")
    return [
        Game(
            id="201",
            awayTeam="Lakers",
            homeTeam="Warriors",
            awayScore=108,
            homeScore=115,
            date=today,
            status="finished"
        ),
        Game(
            id="202",
            awayTeam="Celtics",
            homeTeam="Heat",
            awayScore=None,
            homeScore=None,
            date=today,
            status="scheduled"
        ),
        Game(
            id="203",
            awayTeam="Nuggets",
            homeTeam="Suns",
            awayScore=119,
            homeScore=113,
            date=today,
            status="finished"
        ),
        Game(
            id="204",
            awayTeam="Bucks",
            homeTeam="76ers",
            awayScore=None,
            homeScore=None,
            date=today,
            status="scheduled"
        ),
    ]

# Mock summaries (in production, these would come from LLM generation)
MOCK_SUMMARIES = {
    "101": GameSummary(
        gameId="101",
        summary="The Warriors secured a 115-108 victory over the Lakers in a closely contested matchup. Stephen Curry led all scorers with 32 points, while LeBron James put up 28 points for the Lakers. The game was tied heading into the fourth quarter, but the Warriors pulled away with clutch three-point shooting down the stretch.",
        generatedAt=datetime.now().isoformat()
    ),
    "102": GameSummary(
        gameId="102",
        summary="The Celtics dominated from start to finish, defeating the Heat 122-98. Jayson Tatum scored 35 points and grabbed 12 rebounds, leading Boston to their largest margin of victory this season. Miami struggled with turnovers, committing 18 compared to Boston's 8.",
        generatedAt=datetime.now().isoformat()
    ),
    "103": GameSummary(
        gameId="103",
        summary="In a back-and-forth battle, the Nuggets edged out the Suns 119-113. Nikola Jokic recorded a triple-double with 27 points, 14 rebounds, and 11 assists. Devin Booker scored 38 points for Phoenix, but it wasn't enough as Denver's balanced scoring attack proved too much.",
        generatedAt=datetime.now().isoformat()
    ),
    "201": GameSummary(
        gameId="201",
        summary="The Warriors defeated the Lakers 115-108 in today's matchup. Key performances from Curry and James highlighted an entertaining game.",
        generatedAt=datetime.now().isoformat()
    ),
    "203": GameSummary(
        gameId="203",
        summary="The Nuggets won today's game against the Suns 119-113, with Jokic leading the way.",
        generatedAt=datetime.now().isoformat()
    ),
}

@app.get("/")
def read_root():
    return {"message": "NBA Game Recaps API"}

@app.get("/games/today", response_model=List[Game])
def get_games_today():
    """Returns a list of today's NBA games"""
    return get_todays_games()

@app.get("/games/{game_id}/summary", response_model=GameSummary)
def get_game_summary(game_id: str):
    """Returns the LLM-generated summary for a specific game"""
    if game_id not in MOCK_SUMMARIES:
        raise HTTPException(status_code=404, detail=f"Summary not found for game {game_id}")
    
    return MOCK_SUMMARIES[game_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
