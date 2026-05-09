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


MOOD_ENERGY_GUIDE = {
    "low": "User reports LOW energy today — be gentle, scale the task DOWN, give a tiny minimum-viable version that still keeps the streak. Tone: warm, no pressure.",
    "normal": "User reports NORMAL energy — use the standard difficulty for today. Tone: encouraging, focused.",
    "high": "User reports HIGH energy — push them slightly harder, suggest a bonus stretch action, capitalize on the momentum. Tone: ambitious, fired up.",
}


def generate_daily_plan(goal: dict, stats: dict, mood_energy: str = None) -> str:
    """Generate a daily action plan for the goal based on difficulty, history, and energy."""
    difficulty_label = DIFFICULTY_LABELS.get(goal["difficulty"], "Moderate")
    streak = stats.get("streak", 0)
    completion_rate = stats.get("completion_rate", 0)

    energy_line = ""
    if mood_energy in MOOD_ENERGY_GUIDE:
        energy_line = f"\nEnergy level today: {mood_energy.upper()}\nADAPTATION: {MOOD_ENERGY_GUIDE[mood_energy]}\n"

    prompt = f"""You are a personal accountability coach. Generate a focused daily action plan for the user.

Goal: {goal['title']}
Description: {goal.get('description', 'No description provided')}
Category: {goal.get('category', 'General')}
Difficulty Level: {difficulty_label} ({goal['difficulty']}/5)
Current Streak: {streak} days
Completion Rate: {completion_rate}%
{energy_line}
Create a clear, motivating daily plan with:
1. A single main task for today (specific and actionable, scaled to difficulty AND energy level)
2. Two supporting micro-habits (small actions that reinforce the goal)
3. A one-sentence motivational note tailored to their current streak and energy

Keep it concise — the whole plan should fit in 150 words or less. Use plain text, no markdown headers."""

    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_distraction_insight(goal: dict, insights: dict, recent_check_ins: list) -> str:
    """Analyze distraction patterns and surface actionable insight."""
    if insights["total"] == 0:
        return "No distractions logged yet — start logging when you slip and patterns will emerge."

    top_lines = "\n".join(f"  - {label}: {count}" for label, count in insights["top_sources"][:5])
    time_lines = "\n".join(f"  - {t}: {count}" for t, count in insights["by_time"].items())

    # Cross-reference: which days were missed AND had distractions
    missed_dates = {ci["check_in_date"] for ci in recent_check_ins if not ci["completed"]}

    prompt = f"""You are an accountability coach analyzing where this user keeps slipping.

Goal: {goal['title']}
Total distractions logged (last 30d): {insights['total']}
Days missed in this window: {len(missed_dates)}

Top distraction sources:
{top_lines}

When distractions happen:
{time_lines}

Write 3-4 short sentences:
1. Identify the #1 pattern (e.g. "Social media is your top failure mode, especially at night")
2. Explain WHY this likely keeps happening (root cause, not just observation)
3. Give ONE specific, doable countermeasure (concrete action — like "phone in another room after 9pm")
4. End with a brief encouraging line.

Be direct and specific. No vague platitudes. No bullet points — flowing prose."""

    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=350,
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
        bits = []
        if ci.get("notes"): bits.append(f"note: {ci['notes']}")
        if ci.get("mood_energy"): bits.append(f"energy: {ci['mood_energy']}")
        if ci.get("time_actual_min") and ci.get("time_expected_min"):
            bits.append(f"time {ci['time_actual_min']}m/{ci['time_expected_min']}m")
        suffix = f" — {' · '.join(bits)}" if bits else ""
        history_lines.append(f"  {ci['check_in_date']}: {status}{suffix}")

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
