from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import json
from pathlib import Path
from nba_api.live.nba.endpoints import scoreboard, boxscore

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
    awayTeamId: Optional[int] = None
    homeTeamId: Optional[int] = None
    awayScore: Optional[int] = None
    homeScore: Optional[int] = None
    date: str
    status: str  # "scheduled", "in_progress", "finished"

class GameSummary(BaseModel):
    gameId: str
    summary: str
    generatedAt: str
    awayTeamId: Optional[int] = None
    homeTeamId: Optional[int] = None
    awayTeam: Optional[str] = None
    homeTeam: Optional[str] = None

# Cache directory
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Helper functions for caching and data transformation
def fetch_scoreboard_data() -> Dict[str, Any]:
    """Fetches today's scoreboard data with caching"""
    cache_file = CACHE_DIR / "scoreboard_today.json"
    
    # Check if cached data exists
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache file: {e}")
    
    # Fetch from API
    try:
        scoreboard_obj = scoreboard.ScoreBoard()
        data = scoreboard_obj.get_dict()
        
        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error writing cache file: {e}")
        
        return data
    except Exception as e:
        # If API call fails and we have cached data, try to use it
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to fetch scoreboard data: {str(e)}")

def fetch_boxscore_data(game_id: str) -> Dict[str, Any]:
    """Fetches boxscore data for a specific game with caching"""
    cache_file = CACHE_DIR / f"boxscore_{game_id}.json"
    
    # Check if cached data exists
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache file: {e}")
    
    # Fetch from API
    try:
        boxscore_obj = boxscore.BoxScore(game_id)
        data = boxscore_obj.get_dict()
        
        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error writing cache file: {e}")
        
        return data
    except Exception as e:
        # If API call fails and we have cached data, try to use it
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to fetch boxscore data for game {game_id}: {str(e)}")

def transform_scoreboard_to_games(scoreboard_data: Dict[str, Any]) -> List[Game]:
    """Transforms NBA API scoreboard response to Game models"""
    games = []
    
    if "scoreboard" not in scoreboard_data or "games" not in scoreboard_data["scoreboard"]:
        return games
    
    game_date = scoreboard_data["scoreboard"].get("gameDate", "")
    # Format date from YYYY-MM-DD to "Month DD, YYYY"
    try:
        date_obj = datetime.strptime(game_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
    except:
        formatted_date = game_date
    
    for game_data in scoreboard_data["scoreboard"]["games"]:
        game_id = game_data.get("gameId", "")
        game_status = game_data.get("gameStatus", 1)
        
        # Map gameStatus: 1 = scheduled, 2 = in progress, 3 = finished
        status_map = {
            1: "scheduled",
            2: "in_progress",
            3: "finished"
        }
        status = status_map.get(game_status, "scheduled")
        
        home_team = game_data.get("homeTeam", {})
        away_team = game_data.get("awayTeam", {})
        
        home_team_name = home_team.get("teamName", "")
        away_team_name = away_team.get("teamName", "")
        home_team_id = home_team.get("teamId")
        away_team_id = away_team.get("teamId")
        
        # Get scores (may be 0 for scheduled games)
        home_score = home_team.get("score", 0)
        away_score = away_team.get("score", 0)
        
        # For scheduled games, set scores to None
        # For finished/in_progress games, use the actual scores
        if status == "scheduled":
            home_score = None
            away_score = None
        
        games.append(Game(
            id=game_id,
            awayTeam=away_team_name,
            homeTeam=home_team_name,
            awayTeamId=away_team_id,
            homeTeamId=home_team_id,
            awayScore=away_score,
            homeScore=home_score,
            date=formatted_date,
            status=status
        ))
    
    return games

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
    try:
        scoreboard_data = fetch_scoreboard_data()
        games = transform_scoreboard_to_games(scoreboard_data)
        return games
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching games: {str(e)}")

@app.get("/games/{game_id}/summary", response_model=GameSummary)
def get_game_summary(game_id: str):
    """Returns the LLM-generated summary for a specific game"""
    # For now, we fetch boxscore data to verify the game exists
    # The actual summary generation will be implemented later
    try:
        boxscore_data = fetch_boxscore_data(game_id)
        
        # Extract team info from boxscore data
        home_team_id = None
        away_team_id = None
        home_team_name = None
        away_team_name = None
        if "game" in boxscore_data:
            game_data = boxscore_data["game"]
            if "homeTeam" in game_data:
                home_team = game_data["homeTeam"]
                home_team_id = home_team.get("teamId")
                home_team_name = home_team.get("teamName")
            if "awayTeam" in game_data:
                away_team = game_data["awayTeam"]
                away_team_id = away_team.get("teamId")
                away_team_name = away_team.get("teamName")
        
        # Check if we have a cached summary
        if game_id in MOCK_SUMMARIES:
            summary = MOCK_SUMMARIES[game_id]
            # Add team info to the summary
            summary.awayTeamId = away_team_id
            summary.homeTeamId = home_team_id
            summary.awayTeam = away_team_name
            summary.homeTeam = home_team_name
            return summary
        
        # If no summary exists yet, return a placeholder
        # In the future, this will trigger LLM summary generation
        raise HTTPException(status_code=404, detail=f"Summary not found for game {game_id}. Boxscore data fetched successfully, but summary generation is not yet implemented.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game summary: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
