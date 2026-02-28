from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptPack:
    topic_title: str
    facts: list[str]


def build_prompt_pack(topic_title: str, chunk_texts: list[str]) -> PromptPack:
    # Keep this intentionally small and structured for hackathon prompting.
    facts = []
    for t in chunk_texts:
        t = (t or "").strip()
        if not t:
            continue
        facts.append(t[:600])
    return PromptPack(topic_title=topic_title, facts=facts[:6])

