import os
import anthropic
import streamlit as st

DIFFICULTY_LABELS = {
    1: "Beginner",
    2: "Easy",
    3: "Moderate",
    4: "Challenging",
    5: "Expert",
}


def _get_client():
    """Load API key from Streamlit secrets (cloud) or environment variable (local)."""
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        raise ValueError(
            "No ANTHROPIC_API_KEY found. Add it to .streamlit/secrets.toml or your environment."
        )
    return anthropic.Anthropic(api_key=api_key)


def generate_daily_plan(goal: dict, stats: dict) -> str:
    """Generate a daily action plan for the goal based on difficulty and history."""
    difficulty_label = DIFFICULTY_LABELS.get(goal["difficulty"], "Moderate")
    streak = stats.get("streak", 0)
    completion_rate = stats.get("completion_rate", 0)

    prompt = f"""You are a personal accountability coach. Generate a focused daily action plan for the user.

Goal: {goal['title']}
Description: {goal.get('description', 'No description provided')}
Category: {goal.get('category', 'General')}
Difficulty Level: {difficulty_label} ({goal['difficulty']}/5)
Current Streak: {streak} days
Completion Rate: {completion_rate}%

Create a clear, motivating daily plan with:
1. A single main task for today (specific and actionable, scaled to the difficulty level)
2. Two supporting micro-habits (small actions that reinforce the goal)
3. A one-sentence motivational note tailored to their current streak/progress

Keep it concise — the whole plan should fit in 150 words or less. Use plain text, no markdown headers."""

    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_feedback(goal: dict, stats: dict, recent_check_ins: list) -> str:
    """Generate AI feedback based on user's history and patterns."""
    difficulty_label = DIFFICULTY_LABELS.get(goal["difficulty"], "Moderate")

    # Build a brief history summary
    history_lines = []
    for ci in recent_check_ins[:14]:  # Last 14 days
        status = "Completed" if ci["completed"] else "Missed"
        note = f" — Note: {ci['notes']}" if ci.get("notes") else ""
        history_lines.append(f"  {ci['check_in_date']}: {status}{note}")

    history_text = "\n".join(history_lines) if history_lines else "  No check-ins yet."

    prompt = f"""You are a personal accountability coach giving honest, constructive feedback.

Goal: {goal['title']}
Category: {goal.get('category', 'General')}
Difficulty: {difficulty_label} ({goal['difficulty']}/5)

Stats:
- Current streak: {stats['streak']} days
- Completion rate: {stats['completion_rate']}%
- Consistency score: {stats['consistency_score']}/100
- Missed days: {stats['missed_days']} out of {stats['total_days']} tracked

Recent history:
{history_text}

Write 3-4 sentences of honest, specific feedback:
1. Acknowledge what they're doing well (or encourage if struggling)
2. Identify one clear pattern or issue in their behavior
3. Give one concrete, actionable suggestion for improvement
4. End with a forward-looking motivational statement

Be direct and avoid generic platitudes. Tailor everything to their actual data."""

    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
