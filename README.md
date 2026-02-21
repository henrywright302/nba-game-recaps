# NBA Game Recaps

A web app that turns NBA games into short, readable recaps using official play-by-play data and optional LLM-generated narratives.

## What it does

- **Previous** – Browse games that already have cached recaps. Pick a game to read a concise summary with key moments and standout performances.
- **Today** – See today’s scoreboard (live or cached). Use “Refresh scores” to pull the latest; a 30-minute cooldown prevents overloading the data source.
- Summaries are cached so each game is only processed once; no regeneration on repeat visits.

## Why

I wanted a lightweight way to catch up on NBA games without watching full highlights or scanning raw box scores.

This project focuses on:

- Turning structured sports data into readable narratives
- A simple, clear frontend
- Practical backend design: file-based caching, cooldowns, and optional LLM integration

## Tech

- **Frontend:** React, TypeScript, Vite, React Router
- **Backend:** Python, FastAPI
- **Data:** [nba-api](https://github.com/swar/nba_api) (scoreboard, box scores)
- **Summaries:** OpenAI GPT (optional); without an API key, only pre-cached or manually added summaries are available
- **Storage:** JSON files under `backend/cache/` (no database)

## Getting started

1. **Backend** – From `backend/`, install deps (`pip install -r requirements.txt`), optionally set `OPENAI_API_KEY` via `.env` (see `backend/.env.example`), then run `python main.py`. API at `http://localhost:8000`.
2. **Frontend** – From the repo root, run `npm install` then `npm run dev`. App at `http://localhost:5173`.

See [backend/README.md](backend/README.md) for API details and endpoints.

## Status

In use and iterating. Previous/Today tabs, game recap pages, refresh with cooldown, and LLM summary caching are in place.
