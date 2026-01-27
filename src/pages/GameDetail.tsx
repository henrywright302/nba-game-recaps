import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";

type GameSummary = {
  gameId: string;
  summary: string;
  generatedAt: string;
  awayTeamId: number | null;
  homeTeamId: number | null;
  awayTeam: string | null;
  homeTeam: string | null;
};

function getLogoUrl(teamId: number | null): string {
  if (!teamId) return "";
  return `https://cdn.nba.com/logos/nba/${teamId}/global/L/logo.svg`;
}

function TeamLogo({ teamId, teamName }: { teamId: number | null; teamName: string }) {
  if (!teamId) return <span>{teamName}</span>;
  
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
      <img
        src={getLogoUrl(teamId)}
        alt={`${teamName} logo`}
        loading="lazy"
        style={{
          width: "32px",
          height: "32px",
          objectFit: "contain",
        }}
        onError={(e) => {
          // Fallback: hide image if it fails to load
          e.currentTarget.style.display = "none";
        }}
      />
      <span>{teamName}</span>
    </div>
  );
}

const API_BASE_URL = "http://localhost:8000";

function GameDetail() {
  const { id } = useParams<{ id: string }>();
  const [summary, setSummary] = useState<GameSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      if (!id) return;

      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/games/${id}/summary`);
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Summary not found for this game");
          }
          throw new Error("Failed to fetch game summary");
        }
        
        const data = await response.json();
        setSummary(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        console.error("Error fetching game summary:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
        <Link to="/" style={{ color: "#007bff", textDecoration: "none", marginBottom: "1rem", display: "inline-block" }}>
          ← Back to Dashboard
        </Link>
        <h2>Game Detail</h2>
        <p>Loading game summary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
        <Link to="/" style={{ color: "#007bff", textDecoration: "none", marginBottom: "1rem", display: "inline-block" }}>
          ← Back to Dashboard
        </Link>
        <h2>Game Detail</h2>
        <div style={{ color: "red", marginTop: "1rem" }}>
          <p>Error: {error}</p>
          {error.includes("not found") && (
            <p style={{ fontSize: "0.9rem", marginTop: "0.5rem", color: "#666" }}>
              Summary is not available for game ID: {id}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
        <Link to="/" style={{ color: "#007bff", textDecoration: "none", marginBottom: "1rem", display: "inline-block" }}>
          ← Back to Dashboard
        </Link>
        <h2>Game Detail</h2>
        <p>No summary available.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <Link to="/" style={{ color: "#007bff", textDecoration: "none", marginBottom: "1rem", display: "inline-block" }}>
        ← Back to Dashboard
      </Link>
      <h2>Game Summary</h2>
      {(summary.awayTeam || summary.homeTeam) && (
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          gap: "1rem", 
          marginTop: "1rem",
          marginBottom: "1.5rem",
          paddingBottom: "1rem",
          borderBottom: "1px solid #e0e0e0"
        }}>
          {summary.awayTeam && (
            <TeamLogo teamId={summary.awayTeamId} teamName={summary.awayTeam} />
          )}
          <span style={{ fontSize: "1.2rem", fontWeight: "500" }}>vs</span>
          {summary.homeTeam && (
            <TeamLogo teamId={summary.homeTeamId} teamName={summary.homeTeam} />
          )}
        </div>
      )}
      <div style={{ marginTop: "1.5rem" }}>
        <p style={{ 
          fontSize: "1.1rem", 
          lineHeight: "1.8", 
          color: "#333",
          whiteSpace: "pre-wrap"
        }}>
          {summary.summary}
        </p>
        <div style={{ 
          marginTop: "2rem", 
          paddingTop: "1rem", 
          borderTop: "1px solid #e0e0e0",
          fontSize: "0.85rem",
          color: "#666"
        }}>
          Game ID: {summary.gameId} | Generated: {new Date(summary.generatedAt).toLocaleString()}
        </div>
      </div>
    </div>
  );
}

export default GameDetail;