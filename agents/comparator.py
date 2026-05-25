"""Nano agent: Comparable Devices Similarity Engine.

Uses gpt-5.4-nano with web_search to find and rank comparable
MDR-certified devices per the similarity engine schema.
"""

from __future__ import annotations

import json
import pathlib
from openai import OpenAI
from config import OPENAI_API_KEY, NANO_MODEL

_SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "mdr_comparable_devices_similarity_engine.json"

_SYSTEM = """You are a specialised regulatory-search nano agent.
Your sole task is to find and rank comparable MDR-certified devices
(or MDCG/CJEU/Helsinki Procedure precedented devices) for the
device fact pattern you are given.

You MUST use web search for every comparator you identify.
Parametric recall of device names from training data is prohibited
unless confirmed via web search with a retrievable public URL.

Return your output as a single JSON object with these top-level keys:
  ranked_comparators          – array of 3-4 top matches
  competing_precedents_acknowledged – array (may be empty)
  unavailable_comparators_acknowledged – array (may be empty)
  engine_diagnostic_summary   – object

For each ranked comparator include:
  device_identifier, candidate_url, mdr_class_assigned,
  certifying_notified_body, intended_purpose_verbatim_quote,
  intended_purpose_quote_url, similarity_score_final (0-1),
  match_quality_rating (excellent/good/moderate/poor),
  similarity_drivers_prose, precedent_weight_reasoning_prose,
  transfers_reasoning_to_present_prose, limits_of_transfer_prose,
  rule_applied, sub_clause_applied

Follow the search execution protocol:
  Phase 1 – Discovery: run 5-7 web searches to build a candidate pool
  Phase 2 – Candidate evaluation: for each promising candidate, retrieve
            enough regulatory data to score similarity
  Phase 3 – Score using the weighted dimensions:
            rule_engagement_profile 0.30, intended_purpose_pattern 0.18,
            consequence_chain_severity 0.12, qualification_basis 0.12,
            functional_action_pattern 0.10, guidance_worked_example 0.10,
            user_population_and_setting 0.08
  Phase 4 – Select top 3-4 with diversity consideration
  Phase 5 – Extract detailed evidence per selected match

If you cannot find enough comparators after progressive backoff,
record the gap in unavailable_comparators_acknowledged.

Return ONLY valid JSON. No markdown fences. No commentary outside the JSON."""


def _load_schema_summary() -> str:
    schema = json.loads(_SCHEMA_PATH.read_text())
    return (
        f"Schema: {schema['schema_name']}\n"
        f"Description: {schema['description']}\n"
        f"Active context mode: {schema['context_mode']['active_mode']}\n"
    )


def run_comparator_engine(
    device_description: str,
    intended_purpose: str,
    device_type: str,
    rule_engagement_profile: str,
    consequence_severity: str,
    user_type: str,
    use_environment: str,
    *,
    status_callback=None,
) -> dict:
    """Run the comparator engine nano agent and return structured JSON."""
    client = OpenAI(api_key=OPENAI_API_KEY)

    schema_ctx = _load_schema_summary()

    user_prompt = f"""{schema_ctx}

DEVICE FACT PATTERN FOR COMPARATOR SEARCH
==========================================
Device description: {device_description}
Intended purpose: {intended_purpose}
Device type: {device_type}
Rule engagement profile: {rule_engagement_profile}
Consequence severity tier: {consequence_severity}
User type: {user_type}
Use environment: {use_environment}

Find 3-4 comparable MDR-certified devices using web search.
Return JSON only."""

    if status_callback:
        status_callback("Comparator engine: searching for comparable devices...")

    response = client.responses.create(
        model=NANO_MODEL,
        instructions=_SYSTEM,
        input=[{"role": "user", "content": user_prompt}],
        tools=[{"type": "web_search"}],
    )

    raw_text = response.output_text

    if status_callback:
        status_callback("Comparator engine: parsing results...")

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            result = json.loads(cleaned.strip())
        except json.JSONDecodeError:
            result = {
                "ranked_comparators": [],
                "competing_precedents_acknowledged": [],
                "unavailable_comparators_acknowledged": [],
                "engine_diagnostic_summary": {
                    "error": "Failed to parse nano agent output as JSON",
                    "raw_output": raw_text[:2000],
                },
            }

    return result
