"""Shared tutoring logic: builds grounded system prompts for the tutor, the
grader, and the quiz generator. Used by both the Discord bot (bot.py) and the
local CLI (chat.py) so behavior stays identical everywhere.
"""

import prompts
import rag

MODEL_DEFAULT = "claude-opus-5"

# Appended to every subject persona: how to use retrieved study-library material.
GROUNDING_INSTRUCTIONS = """
--- Using the study library ---
Below you may be given a STUDY LIBRARY CONTEXT block: excerpts retrieved from a
library of AP rubrics, scored sample responses, and the student's own uploaded notes.
When it's relevant to the question:
- Cite the specific rubric criterion by name (e.g., "DBQ · Complexity (1 pt)").
- When a scored sample is relevant, reference it and explain *why* it earned (or lost)
  its score — connect the student's situation to that example.
- Prefer the retrieved material over generic advice for anything about scoring.
- Samples labeled "scored sample" in the built-in library are illustrative/synthetic
  teaching examples, not official College Board samples — you may say so if asked.
  Material labeled "your upload" is the student's own file.
If the context doesn't cover something, use your general AP knowledge and say the
library didn't have specifics on it. Never invent a rubric point value or a fake
"official sample" — only cite what's actually provided or well-established.
"""


def _with_context(subject_key: str, base_system: str, retrieval_query: str) -> str:
    """Attach grounding instructions + retrieved library excerpts to a system prompt."""
    system = base_system + GROUNDING_INSTRUCTIONS
    context_block = rag.build_context(subject_key, retrieval_query)
    if context_block:
        system += "\n\n" + context_block
    return system


def tutor_system(subject_key: str, user_text: str) -> str:
    """System prompt for a normal tutoring turn."""
    _, base = prompts.SUBJECTS[subject_key]
    return _with_context(subject_key, base, user_text)


def grade_system(subject_key: str, work: str) -> str:
    """System prompt for grading a piece of student writing against the rubric."""
    _, base = prompts.SUBJECTS[subject_key]
    grading = base + """
--- Grading mode ---
The student has submitted a piece of their own writing (a thesis, paragraph, SAQ
answer, or essay excerpt). Grade it constructively against the relevant rubric:
1. Identify which rubric criteria apply to this kind of writing.
2. For EACH applicable criterion, state its name, say whether it is currently
   Earned / Partially there / Not yet earned, and give one concrete, specific fix.
3. If helpful, compare it to a scored sample from the library and explain the gap.
4. End with "**Biggest win:**" and the single highest-impact change they could make.
Be honest but encouraging — the goal is a better next draft, not a grade to submit.
Do NOT rewrite the work for them; coach them to improve it themselves.
"""
    return _with_context(subject_key, grading, work)


def quiz_system(subject_key: str, topic: str = "") -> str:
    """System prompt for generating one realistic AP practice item."""
    _, base = prompts.SUBJECTS[subject_key]
    if subject_key == "euro":
        kinds = ("a DBQ prompt, an LEQ prompt, an SAQ (three parts), or a "
                 "stimulus-based source-analysis question")
    else:  # seminar
        kinds = ("a source-analysis question (analyze an author's argument/reasoning), "
                 "a 'build an argument from sources' prompt, or a research-question "
                 "brainstorming exercise")
    focus = f" Focus the item on this topic: {topic}." if topic.strip() else ""
    quiz = base + f"""
--- Quiz mode ---
Generate ONE realistic AP practice item for this student. Choose an appropriate
format ({kinds}).{focus}
- Make it exam-realistic in style and difficulty.
- State clearly what the task is asking and, briefly, which rubric skills it targets.
- Do NOT provide the answer yet. End by inviting the student to post their attempt,
  and tell them they can then ask you to grade it or give hints.
Keep it concise enough to read comfortably in a Discord message.
"""
    return _with_context(subject_key, quiz, topic or subject_key)


def extract_text(response) -> str:
    """Pull the plain-text answer out of a Messages API response."""
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    return text or "Hmm, I didn't have a good answer for that — try rephrasing?"
