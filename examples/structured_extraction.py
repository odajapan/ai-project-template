"""Extract structured data from text using a Pydantic schema.

Run::

    python examples/structured_extraction.py
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

from your_project_name.llm import ClaudeClient
from your_project_name.schemas import StructuredResponse

load_dotenv()


class IssueSummary(StructuredResponse):
    title: str
    severity: str  # "low" | "medium" | "high" | "critical"
    affected_components: list[str]
    suggested_fix: str


SCHEMA_HINT = json.dumps(
    {
        "title": "string — short title under 60 chars",
        "severity": "low | medium | high | critical",
        "affected_components": ["component name", "..."],
        "suggested_fix": "one-sentence fix recommendation",
    },
    indent=2,
)


SYSTEM_PROMPT = (
    "You extract structured issue summaries from bug reports. "
    "Reply with JSON only — no prose, no code fences. "
    f"Schema:\n{SCHEMA_HINT}"
)


BUG_REPORT = """
The dashboard's revenue chart shows zero for all dates between 2024-12-01
and 2024-12-15. Confirmed across staging and production. Other charts
(orders, refunds) render correctly. Likely a regression introduced when
the BillingService aggregator was refactored last week.
"""


def main() -> None:
    client = ClaudeClient(system=SYSTEM_PROMPT, max_tokens=512)
    raw = client.chat(BUG_REPORT)

    summary = IssueSummary.from_text(raw)
    assert isinstance(summary, IssueSummary)

    print(f"Title:      {summary.title}")
    print(f"Severity:   {summary.severity}")
    print(f"Components: {', '.join(summary.affected_components)}")
    print(f"Fix:        {summary.suggested_fix}")


if __name__ == "__main__":
    main()
