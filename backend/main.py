from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel
import json
import time
from pathlib import Path
from math import ceil
from nba_api.live.nba.endpoints import scoreboard, boxscore

from relevance_filter import generate_llm_prompt
from llm_service import (
    load_cached_summary,
    save_cached_summary,
    generate_summary as llm_generate_summary,
    validate_api_key,
)

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

REFRESH_COOLDOWN_SECONDS = 30 * 60  # 30 minutes
SCOREBOARD_REFRESHED_AT_FILE = CACHE_DIR / "scoreboard_today_refreshed_at.txt"

# Helper functions for caching and data transformation
def fetch_scoreboard_data() -> Dict[str, Any]:
    """Fetches today's scoreboard data with caching. Use GET /games/today/refresh to overwrite cache."""
    cache_file = CACHE_DIR / "scoreboard_today.json"
    today = datetime.now().strftime("%Y-%m-%d")

    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            cached_date = data.get("scoreboard", {}).get("gameDate")
            if cached_date == today:
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache file: {e}")

    # Fetch from API (cache miss or wrong date)
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
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to fetch scoreboard data: {str(e)}")


SUMMARY_CACHE_DIR = CACHE_DIR / "summaries"

def _game_from_boxscore_data(data: Dict[str, Any]) -> Optional[Tuple[datetime, Game]]:
    """Build a Game from boxscore dict; returns None if missing required fields."""
    status_map = {1: "scheduled", 2: "in_progress", 3: "finished"}
    g = data.get("game") or {}
    game_id = g.get("gameId")
    if not game_id:
        return None
    ht = g.get("homeTeam") or {}
    at = g.get("awayTeam") or {}
    game_status = g.get("gameStatus", 3)
    status = status_map.get(game_status, "finished")
    game_time = g.get("gameTimeLocal") or g.get("gameEt") or ""
    date_str = game_time[:10] if len(game_time) >= 10 else ""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.min
        formatted_date = date_obj.strftime("%B %d, %Y")
    except Exception:
        formatted_date = date_str or ""
        date_obj = datetime.min
    return (
        date_obj,
        Game(
            id=game_id,
            awayTeam=at.get("teamName", ""),
            homeTeam=ht.get("teamName", ""),
            awayTeamId=at.get("teamId"),
            homeTeamId=ht.get("teamId"),
            awayScore=at.get("score"),
            homeScore=ht.get("score"),
            date=formatted_date,
            status=status,
        ),
    )


def games_from_boxscore_cache() -> List[Game]:
    """Build list of games from cached boxscore_*.json files (latest first). Uses only nba-api cache."""
    entries: List[tuple] = []
    for path in CACHE_DIR.glob("boxscore_*.json"):
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        entry = _game_from_boxscore_data(data)
        if entry:
            entries.append(entry)
    entries.sort(key=lambda x: x[0], reverse=True)
    return [game for _, game in entries]


def games_with_cached_summaries() -> List[Game]:
    """Build list of games that have a cached summary (summary_*.json). Uses boxscore cache for details."""
    entries: List[tuple] = []
    SUMMARY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for path in SUMMARY_CACHE_DIR.glob("summary_*.json"):
        game_id = path.stem.replace("summary_", "", 1)
        if not game_id:
            continue
        boxscore_path = CACHE_DIR / f"boxscore_{game_id}.json"
        if not boxscore_path.exists():
            continue
        try:
            with open(boxscore_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        entry = _game_from_boxscore_data(data)
        if entry:
            entries.append(entry)
    entries.sort(key=lambda x: x[0], reverse=True)
    return [game for _, game in entries]


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
    """Returns a list of today's NBA games (from cache)."""
    try:
        scoreboard_data = fetch_scoreboard_data()
        games = transform_scoreboard_to_games(scoreboard_data)
        return games
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching games: {str(e)}")


@app.get("/games/today/refresh")
def refresh_games_today():
    """Calls NBA scoreboard again and overwrites today's cache. 30-minute cooldown between refreshes."""
    from fastapi.responses import JSONResponse

    now = time.time()
    if SCOREBOARD_REFRESHED_AT_FILE.exists():
        try:
            last = float(SCOREBOARD_REFRESHED_AT_FILE.read_text().strip())
            elapsed = now - last
            if elapsed < REFRESH_COOLDOWN_SECONDS:
                seconds_left = int(REFRESH_COOLDOWN_SECONDS - elapsed)
                minutes_left = ceil(seconds_left / 60)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Refresh on cooldown. Try again in {minutes_left} minute(s).",
                        "retryAfterSeconds": seconds_left,
                    },
                    headers={"Retry-After": str(seconds_left)},
                )
        except (ValueError, OSError):
            pass

    cache_file = CACHE_DIR / "scoreboard_today.json"
    try:
        scoreboard_obj = scoreboard.ScoreBoard()
        data = scoreboard_obj.get_dict()
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)
        SCOREBOARD_REFRESHED_AT_FILE.write_text(str(now))
        return transform_scoreboard_to_games(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh scoreboard: {str(e)}")


@app.get("/games/previous", response_model=List[Game])
def get_games_previous():
    """Returns only games that have a cached summary (summary_*.json). Uses boxscore cache for details."""
    try:
        return games_with_cached_summaries()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading previous games: {str(e)}")


def _extract_team_info(boxscore_data: Dict[str, Any]) -> tuple:
    """Extract home/away team ids and names from boxscore. Returns (away_*, home_*)."""
    home_team_id = away_team_id = home_team_name = away_team_name = None
    if "game" not in boxscore_data:
        return away_team_id, away_team_name, home_team_id, home_team_name
    game_data = boxscore_data["game"]
    if "homeTeam" in game_data:
        ht = game_data["homeTeam"]
        home_team_id = ht.get("teamId")
        home_team_name = ht.get("teamName")
    if "awayTeam" in game_data:
        at = game_data["awayTeam"]
        away_team_id = at.get("teamId")
        away_team_name = at.get("teamName")
    return away_team_id, away_team_name, home_team_id, home_team_name


def _cached_to_game_summary(cached: Dict[str, Any]) -> GameSummary:
    """Build GameSummary from cached summary dict."""
    return GameSummary(
        gameId=cached.get("gameId", ""),
        summary=cached["summary"],
        generatedAt=cached.get("generatedAt", ""),
        awayTeamId=cached.get("awayTeamId"),
        homeTeamId=cached.get("homeTeamId"),
        awayTeam=cached.get("awayTeam"),
        homeTeam=cached.get("homeTeam"),
    )


@app.get("/games/{game_id}/summary", response_model=GameSummary)
def get_game_summary(game_id: str):
    """Returns the LLM-generated summary for a specific game. Cached forever; no regeneration."""
    try:
        # 1. Check file cache first (forever cache)
        cached = load_cached_summary(game_id)
        if cached:
            return _cached_to_game_summary(cached)

        # 2. Legacy mock summaries
        if game_id in MOCK_SUMMARIES:
            boxscore_data = fetch_boxscore_data(game_id)
            away_team_id, away_team_name, home_team_id, home_team_name = _extract_team_info(boxscore_data)
            summary = MOCK_SUMMARIES[game_id]
            summary.awayTeamId = away_team_id
            summary.homeTeamId = home_team_id
            summary.awayTeam = away_team_name
            summary.homeTeam = home_team_name
            return summary

        # 3. Fetch boxscore and generate via LLM (then cache forever)
        boxscore_data = fetch_boxscore_data(game_id)
        away_team_id, away_team_name, home_team_id, home_team_name = _extract_team_info(boxscore_data)

        game_data = boxscore_data.get("game", {})
        game_status = game_data.get("gameStatus")
        if game_status != 3:
            raise HTTPException(
                status_code=400,
                detail=f"Summary only available for finished games. Game {game_id} status is not final.",
            )

        if not validate_api_key():
            raise HTTPException(
                status_code=503,
                detail="Summary generation is not configured. Set OPENAI_API_KEY in backend/.env (see .env.example).",
            )

        prompt = generate_llm_prompt(boxscore_data)
        summary_text, prompt_tokens, completion_tokens = llm_generate_summary(prompt)
        generated_at = datetime.utcnow().isoformat() + "Z"

        save_cached_summary(
            game_id=game_id,
            summary=summary_text,
            generated_at=generated_at,
            away_team_id=away_team_id,
            home_team_id=home_team_id,
            away_team=away_team_name,
            home_team=home_team_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        return GameSummary(
            gameId=game_id,
            summary=summary_text,
            generatedAt=generated_at,
            awayTeamId=away_team_id,
            homeTeamId=home_team_id,
            awayTeam=away_team_name,
            homeTeam=home_team_name,
        )
    except HTTPException:
        raise
    except ValueError as e:
        if "OPENAI_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        detail = str(e) if str(e) else "Summary generation temporarily unavailable. Please try again later."
        raise HTTPException(status_code=503, detail=detail)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
