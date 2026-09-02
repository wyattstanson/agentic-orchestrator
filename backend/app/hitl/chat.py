"""The clarifying chat panel — let a human question the agent before deciding."""

from __future__ import annotations

from .queue import ApprovalRequest


def answer_question(request: ApprovalRequest, question: str) -> str:
    from app.config import get_settings
    from app.llm import Message, get_provider

    provider = get_provider()
    model = get_settings().llm_model_reviewer
    msgs = [
        Message(
            role="system",
            content=(
                "You are the agent that proposed this action, awaiting human "
                "approval. Answer the reviewer's question concisely and honestly, "
                "using only the context you have."
            ),
        ),
        Message(
            role="user",
            content=(
                f"Task: {request.task_id}\n"
                f"Why this was escalated: {request.reason}\n"
                f"Proposed action / output:\n{request.proposed_action}\n"
                f"My reasoning: {request.agent_reasoning}\n\n"
                f"Reviewer's question: {question}"
            ),
        ),
    ]
    return provider.complete(msgs, model=model, temperature=0.3, max_tokens=500).text
