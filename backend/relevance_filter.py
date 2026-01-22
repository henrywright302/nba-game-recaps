"""
Rule-based relevance filter for NBA game statistics.
Extracts key statistics from game data to create focused LLM prompts.
"""

from datetime import datetime
from typing import Dict, List, Any


def determine_time_of_day(game_time_local: str) -> str:
    """
    Determines if game was morning, afternoon, or evening based on local time.
    
    Args:
        game_time_local: ISO format datetime string (e.g., "2021-01-15T19:30:00-05:00")
    
    Returns:
        "morning", "afternoon", or "evening"
    """
    try:
        # Parse the datetime string (handles timezone offset)
        dt = datetime.fromisoformat(game_time_local.replace('Z', '+00:00'))
        hour = dt.hour
        
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    except (ValueError, AttributeError):
        # Default to evening if parsing fails
        return "evening"


def extract_team_statistics(team_data: Dict[str, Any], team_type: str) -> List[str]:
    """
    Extracts relevant statistics for a team.
    
    Args:
        team_data: Team data dictionary from the game JSON
        team_type: "home" or "away"
    
    Returns:
        List of formatted statistic strings
    """
    stats = []
    team_name = f"{team_data.get('teamCity', '')} {team_data.get('teamName', '')}".strip()
    team_stats = team_data.get('statistics', {})
    
    # Basic team info
    score = team_data.get('score', 0)
    stats.append(f"{team_name}: {score} points")
    
    # Bench points
    bench_points = team_stats.get('benchPoints', 0)
    if bench_points > 0:
        stats.append(f"{team_name} bench: {bench_points} points")
    
    # Biggest lead
    biggest_lead = team_stats.get('biggestLead', 0)
    if biggest_lead > 0:
        lead_score = team_stats.get('biggestLeadScore', '')
        point_word = "point" if biggest_lead == 1 else "points"
        stats.append(f"{team_name} biggest lead: {biggest_lead} {point_word} ({lead_score})")
    
    # Rebounds breakdown
    rebounds_offensive = team_stats.get('reboundsOffensive', 0)
    rebounds_defensive = team_stats.get('reboundsDefensive', 0)
    rebounds_total = team_stats.get('reboundsTotal', 0)
    stats.append(f"{team_name} rebounds: {rebounds_total} total ({rebounds_offensive} offensive, {rebounds_defensive} defensive)")
    
    # Turnovers
    turnovers_total = team_stats.get('turnoversTotal', 0)
    stats.append(f"{team_name} turnovers: {turnovers_total}")
    
    # Additional relevant statistics
    # Field goal percentage (if notable - very high or very low)
    fg_percentage = team_stats.get('fieldGoalsPercentage', 0)
    if fg_percentage > 0.5 or fg_percentage < 0.4:
        stats.append(f"{team_name} field goal percentage: {fg_percentage:.1%}")
    
    # Three-point percentage (if notable)
    three_pt_percentage = team_stats.get('threePointersPercentage', 0)
    three_pt_made = team_stats.get('threePointersMade', 0)
    if three_pt_percentage > 0.4 or (three_pt_percentage < 0.25 and three_pt_made > 5):
        stats.append(f"{team_name} three-pointers: {three_pt_made} made ({three_pt_percentage:.1%})")
    
    # Fast break points (if significant)
    fast_break_points = team_stats.get('pointsFastBreak', 0)
    if fast_break_points >= 15:
        stats.append(f"{team_name} fast break points: {fast_break_points}")
    
    # Points from turnovers (defensive impact)
    points_from_turnovers = team_stats.get('pointsFromTurnovers', 0)
    if points_from_turnovers >= 15:
        stats.append(f"{team_name} points off turnovers: {points_from_turnovers}")
    
    return stats


def calculate_game_context(home_team: Dict[str, Any], away_team: Dict[str, Any]) -> List[str]:
    """
    Calculates game-level context statistics.
    
    Args:
        home_team: Home team data dictionary
        away_team: Away team data dictionary
    
    Returns:
        List of formatted context statistic strings
    """
    context_stats = []
    home_stats = home_team.get('statistics', {})
    away_stats = away_team.get('statistics', {})
    
    # Point differential
    home_score = home_team.get('score', 0)
    away_score = away_team.get('score', 0)
    point_diff = abs(home_score - away_score)
    point_word = "point" if point_diff == 1 else "points"
    
    if point_diff <= 5:
        context_stats.append(f"Game was decided by {point_diff} {point_word} (close game)")
    elif point_diff <= 10:
        context_stats.append(f"Game was decided by {point_diff} {point_word}")
    else:
        context_stats.append(f"Game was decided by {point_diff} {point_word} (blowout)")
    
    # Lead changes
    lead_changes = home_stats.get('leadChanges', 0)
    if lead_changes > 5:
        context_stats.append(f"Game featured {lead_changes} lead changes (back-and-forth)")
    elif lead_changes > 0:
        context_stats.append(f"Game had {lead_changes} lead change(s)")
    
    # Rebounding advantage
    home_rebounds = home_stats.get('reboundsTotal', 0)
    away_rebounds = away_stats.get('reboundsTotal', 0)
    rebound_diff = abs(home_rebounds - away_rebounds)
    
    if rebound_diff >= 10:
        winner = "home" if home_rebounds > away_rebounds else "away"
        context_stats.append(f"{winner.capitalize()} team dominated rebounding (+{rebound_diff} rebounds)")
    
    # Turnover differential
    home_turnovers = home_stats.get('turnoversTotal', 0)
    away_turnovers = away_stats.get('turnoversTotal', 0)
    turnover_diff = abs(home_turnovers - away_turnovers)
    
    if turnover_diff >= 5:
        winner = "home" if home_turnovers < away_turnovers else "away"
        context_stats.append(f"{winner.capitalize()} team had {turnover_diff} fewer turnovers")
    
    return context_stats


def filter_relevant_statistics(game_data: Dict[str, Any]) -> List[str]:
    """
    Main function to filter and extract relevant statistics from game data.
    
    Args:
        game_data: Full game data dictionary from the JSON
    
    Returns:
        List of formatted statistic strings for the LLM prompt
    """
    relevant_stats = []
    game = game_data.get('game', {})
    
    # Game time context
    game_time_local = game.get('gameTimeLocal', '')
    if game_time_local:
        time_of_day = determine_time_of_day(game_time_local)
        relevant_stats.append(f"Game was played in the {time_of_day}")
    
    # Arena information
    arena = game.get('arena', {})
    arena_name = arena.get('arenaName', '')
    arena_city = arena.get('arenaCity', '')
    if arena_name and arena_city:
        relevant_stats.append(f"Venue: {arena_name} in {arena_city}")
    
    # Sellout status
    sellout = game.get('sellout', '0')
    if str(sellout) == '1' or sellout is True:
        relevant_stats.append("Arena was sold out")
    
    # Team statistics
    home_team = game.get('homeTeam', {})
    away_team = game.get('awayTeam', {})
    
    # Extract statistics for both teams
    home_stats = extract_team_statistics(home_team, 'home')
    away_stats = extract_team_statistics(away_team, 'away')
    
    relevant_stats.extend(home_stats)
    relevant_stats.extend(away_stats)
    
    # Game-level context
    context_stats = calculate_game_context(home_team, away_team)
    relevant_stats.extend(context_stats)
    
    return relevant_stats


def generate_llm_prompt(game_data: Dict[str, Any], tone: str = "neutral, ESPN-style") -> str:
    """
    Generates a formatted LLM prompt with relevant statistics.
    
    Args:
        game_data: Full game data dictionary from the JSON
        tone: Desired tone for the recap (default: "neutral, ESPN-style")
    
    Returns:
        Formatted prompt string ready for LLM
    """
    relevant_stats = filter_relevant_statistics(game_data)
    
    # Format statistics as bullet points
    facts_section = "\n".join([f"- {stat}" for stat in relevant_stats])
    
    prompt = f"""Write a professional NBA recap paragraph.

Facts:
{facts_section}

Tone: {tone}"""
    
    return prompt


def generate_llm_prompt_from_file(json_file_path: str, tone: str = "neutral, ESPN-style") -> str:
    """
    Convenience function to generate prompt from a JSON file.
    
    Args:
        json_file_path: Path to the JSON file containing game data
        tone: Desired tone for the recap
    
    Returns:
        Formatted prompt string ready for LLM
    """
    import json
    
    with open(json_file_path, 'r') as f:
        game_data = json.load(f)
    
    return generate_llm_prompt(game_data, tone)
