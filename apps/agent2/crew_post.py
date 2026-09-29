"""Agent2 product: post draft crew (Researcher → Writer → Editor) via LiteLLM."""
from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from llm import make_llm
from prompts import (
    EDIT_EXPECTED,
    EDITOR_BACKSTORY,
    EDITOR_GOAL,
    EDITOR_ROLE,
    RESEARCH_EXPECTED,
    RESEARCHER_BACKSTORY,
    RESEARCHER_GOAL,
    RESEARCHER_ROLE,
    WRITE_EXPECTED,
    WRITER_BACKSTORY,
    WRITER_GOAL,
    WRITER_ROLE,
    edit_task_description,
    research_task_description,
    write_task_description,
)


def build_post_crew(topic: str, *, verbose: bool = True) -> Crew:
    llm = make_llm()

    researcher = Agent(
        role=RESEARCHER_ROLE,
        goal=RESEARCHER_GOAL,
        backstory=RESEARCHER_BACKSTORY,
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )
    writer = Agent(
        role=WRITER_ROLE,
        goal=WRITER_GOAL,
        backstory=WRITER_BACKSTORY,
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )
    editor = Agent(
        role=EDITOR_ROLE,
        goal=EDITOR_GOAL,
        backstory=EDITOR_BACKSTORY,
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    research = Task(
        description=research_task_description(topic),
        expected_output=RESEARCH_EXPECTED,
        agent=researcher,
    )
    write = Task(
        description=write_task_description(topic),
        expected_output=WRITE_EXPECTED,
        agent=writer,
        context=[research],
    )
    edit = Task(
        description=edit_task_description(topic),
        expected_output=EDIT_EXPECTED,
        agent=editor,
        context=[research, write],
    )

    return Crew(
        agents=[researcher, writer, editor],
        tasks=[research, write, edit],
        process=Process.sequential,
        verbose=verbose,
        tracing=False,
    )


def run_post_draft(topic: str, *, verbose: bool = True) -> str:
    """Run the crew and return the final post text."""
    crew = build_post_crew(topic, verbose=verbose)
    result = crew.kickoff()
    text = getattr(result, "raw", None) or str(result)
    return (text or "").strip()
