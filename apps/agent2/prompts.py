"""Minimal prompts for the post-draft crew (scenario details TBD)."""

RESEARCHER_ROLE = "Researcher"
RESEARCHER_GOAL = "Gather clear talking points and angle for a short social post."
RESEARCHER_BACKSTORY = (
    "You research topics quickly and list facts, hooks, and audience angles. "
    "You do not write the final post."
)

WRITER_ROLE = "Writer"
WRITER_GOAL = "Draft a readable social-media post from the research brief."
WRITER_BACKSTORY = (
    "You write concise posts with a clear hook and one call to action. "
    "You follow the research brief without inventing unrelated claims."
)

EDITOR_ROLE = "Editor"
EDITOR_GOAL = "Polish the draft into a publication-ready post."
EDITOR_BACKSTORY = (
    "You edit for clarity, tone, and length. You return only the final post text, "
    "no meta commentary."
)


def research_task_description(topic: str) -> str:
    return (
        f"Topic / brief: {topic}\n\n"
        "Produce a short research brief: audience, 3–5 key points, suggested angle, "
        "and any risks (claims that need soft wording). No full post yet."
    )


RESEARCH_EXPECTED = "A structured research brief in plain text."


def write_task_description(topic: str) -> str:
    return (
        f"Original topic / brief: {topic}\n\n"
        "Using the research brief, write one draft social post "
        "(roughly 80–200 words unless the topic clearly needs otherwise)."
    )


WRITE_EXPECTED = "A complete draft post in plain text."


def edit_task_description(topic: str) -> str:
    return (
        f"Original topic / brief: {topic}\n\n"
        "Edit the draft into the final post. Fix grammar and flow; keep the hook and CTA. "
        "Output ONLY the final post text."
    )


EDIT_EXPECTED = "The final post text only."
