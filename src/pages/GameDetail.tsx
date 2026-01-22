import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";

type GameSummary = {
  gameId: string;
  summary: string;
  generatedAt: string;
};

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