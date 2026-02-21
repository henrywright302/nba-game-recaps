import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import "./Dashboard.css";

type Game = {
  id: string;
  awayTeam: string;
  homeTeam: string;
  awayTeamId: number | null;
  homeTeamId: number | null;
  awayScore: number | null;
  homeScore: number | null;
  date: string;
  status: string;
};

function getLogoUrl(teamId: number | null): string {
  if (!teamId) return "";
  return `https://cdn.nba.com/logos/nba/${teamId}/global/L/logo.svg`;
}

function TeamLogo({ teamId, teamName }: { teamId: number | null; teamName: string }) {
  if (!teamId) return <span className="team-name">{teamName}</span>;
  
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
      <img
        src={getLogoUrl(teamId)}
        alt={`${teamName} logo`}
        loading="lazy"
        style={{
          width: "24px",
          height: "24px",
          objectFit: "contain",
        }}
        onError={(e) => {
          // Fallback: hide image if it fails to load
          e.currentTarget.style.display = "none";
        }}
      />
      <span className="team-name">{teamName}</span>
    </div>
  );
}

const API_BASE_URL = "http://localhost:8000";

type Tab = "previous" | "today";

export default function Dashboard() {
  const [tab, setTab] = useState<Tab>("previous");
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshCooldownSeconds, setRefreshCooldownSeconds] = useState(0);

  const fetchGames = async () => {
    const endpoint =
      tab === "previous"
        ? `${API_BASE_URL}/games/previous`
        : `${API_BASE_URL}/games/today`;
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error("Failed to fetch games");
      }
      const data = await response.json();
      setGames(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Error fetching games:", err);
    } finally {
      setLoading(false);
    }
  };

  const refreshTodayScores = async () => {
    if (refreshCooldownSeconds > 0) return;
    setRefreshError(null);
    setRefreshing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/games/today/refresh`);
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = (body as { detail?: string }).detail ?? "Failed to refresh";
        const retryAfter = (body as { retryAfterSeconds?: number }).retryAfterSeconds;
        setRefreshError(detail);
        if (response.status === 429 && typeof retryAfter === "number") {
          setRefreshCooldownSeconds(Math.max(1, retryAfter));
        }
        return;
      }
      setGames(body);
      setRefreshCooldownSeconds(0);
    } catch (err) {
      setRefreshError(err instanceof Error ? err.message : "An error occurred");
      console.error("Error refreshing scores:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    setRefreshError(null);
    fetchGames();
  }, [tab]);

  useEffect(() => {
    if (refreshCooldownSeconds <= 0) return;
    const id = setInterval(() => {
      setRefreshCooldownSeconds((s) => (s <= 1 ? 0 : s - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [refreshCooldownSeconds]);

  if (loading) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <h1>NBA Game Recaps</h1>
          <p className="dashboard-subtitle">
            Browse recent game recaps and highlights
          </p>
        </header>
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <p>Loading games...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <h1>NBA Game Recaps</h1>
          <p className="dashboard-subtitle">
            Browse recent game recaps and highlights
          </p>
        </header>
        <div style={{ textAlign: "center", padding: "2rem", color: "red" }}>
          <p>Error: {error}</p>
          <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Make sure the backend server is running on port 8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>NBA Game Recaps</h1>
        <p className="dashboard-subtitle">
          Catch up with quick recaps from last night
        </p>
      </header>

      <div className="dashboard-tabs-row">
        <nav className="dashboard-tabs" aria-label="Switch date">
          <button
            type="button"
            className={`dashboard-tab ${tab === "previous" ? "dashboard-tab-active" : ""}`}
            onClick={() => setTab("previous")}
          >
            Previous
          </button>
          <button
            type="button"
            className={`dashboard-tab ${tab === "today" ? "dashboard-tab-active" : ""}`}
            onClick={() => setTab("today")}
          >
            Today
          </button>
        </nav>
        {tab === "today" && (
          <div className="dashboard-refresh-wrap">
            <button
              type="button"
              className="dashboard-refresh"
              onClick={refreshTodayScores}
              disabled={refreshing || refreshCooldownSeconds > 0}
            >
              {refreshing
                ? "Refreshing..."
                : refreshCooldownSeconds > 0
                  ? `Refresh in ${Math.ceil(refreshCooldownSeconds / 60)} min`
                  : "Refresh scores"}
            </button>
            {refreshError && (
              <p className="dashboard-refresh-error" role="alert">
                {refreshError}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="games-grid">
        {games.map((game) => (
          <Link
            key={game.id}
            to={`/game/${game.id}`}
            className="game-card"
          >
            <div className="game-card-content">
              <div className="game-teams">
                <div className="team-row">
                  <TeamLogo teamId={game.awayTeamId} teamName={game.awayTeam} />
                  <span className="team-score">
                    {game.awayScore !== null ? game.awayScore : "-"}
                  </span>
                </div>
                <div className="team-row">
                  <TeamLogo teamId={game.homeTeamId} teamName={game.homeTeam} />
                  <span className="team-score">
                    {game.homeScore !== null ? game.homeScore : "-"}
                  </span>
                </div>
              </div>
              <div className="game-date">{game.date}</div>
              <div
                style={{
                  fontSize: "0.75rem",
                  color: "#666",
                  marginTop: "0.5rem",
                  textTransform: "capitalize",
                }}
              >
                {game.status.replace("_", " ")}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
