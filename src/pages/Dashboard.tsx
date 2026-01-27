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

export default function Dashboard() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGames = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/games/today`);
        if (!response.ok) {
          throw new Error("Failed to fetch games");
        }
        const data = await response.json();
        setGames(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        console.error("Error fetching games:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchGames();
  }, []);

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
          Browse recent game recaps and highlights
        </p>
      </header>

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
