# NBA Game Recaps Backend

FastAPI backend for the NBA Game Recaps application.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /games/today` - Returns a list of today's NBA games
- `GET /games/{game_id}/summary` - Returns the LLM-generated summary for a specific game

## API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
