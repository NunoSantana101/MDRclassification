"""Orchestrator agent: MDR Classification Composition.

Uses gpt-5.4-mini with the Responses API. Defines two function tools
that map to the nano agents (comparator engine and regulatory search).
Composes the final v4 schema JSON output.
"""

from __future__ import annotations

import json
import pathlib
import uuid
from datetime import datetime, timezone
from openai import OpenAI
from config import OPENAI_API_KEY, ORCHESTRATOR_MODEL
from agents.comparator import run_comparator_engine
from agents.regulatory import run_regulatory_search

_V4_SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "MDR_classification_schema_v4.json"

_SYSTEM = """You are an MDR classification orchestrator agent.
You produce a structured JSON output conforming to the
MDR_classification_schema_v4 for any medical device fact pattern.

YOUR WORKFLOW:
1. Analyse the device parameters provided by the user.
2. Call run_regulatory_search to retrieve Annex VIII rule texts and
   relevant guidance — it searches the vector store first (contains MDR
   full text, MDCG 2019-11, ISO 13485:2016), then uses web search for
   additional sources and update checks.
3. Using the retrieved regulatory sources, perform rule-by-rule
   assessment of all 22 Annex VIII rules.
4. Call run_comparator_engine to find and rank comparable MDR-certified
   devices using the similarity engine.
5. Compose the final classification output as a single JSON object
   conforming to the v4 schema.

CRITICAL CONSTRAINTS:
- You MUST call both tools. Do not skip regulatory search or
  comparator search.
- All 22 Annex VIII rules must be assessed (section_6 must have
  exactly 22 entries).
- Use verbatim regulatory text from the regulatory search results,
  not from your training data.
- The classification is PROVISIONAL — human review is always required.
- Set human_review_required to true always.
- Surface interpretive uncertainties honestly; do not resolve them
  deterministically.

VERBOSITY: LOW. All prose fields: short, factual, direct sentences.
No filler phrases, no restating inputs, no padding. Meet minLength
requirements with substance, not volume.

OUTPUT FORMAT:
Return a single JSON object with all required v4 schema fields.
No markdown fences. No commentary outside the JSON."""


ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "name": "run_regulatory_search",
        "description": (
            "Retrieve regulatory sources using two-phase retrieval. "
            "Phase 1: file_search on vector store containing MDR full text "
            "(Regulation (EU) 2017/745 including all Annexes), MDCG 2019-11 "
            "(software qualification), and ISO 13485:2016. "
            "Phase 2: web_search for sources not in the store (CJEU rulings, "
            "Borderline Manual, Team-NB, other MDCG guidance, EUDAMED) and "
            "update checks on store contents. "
            "Returns verbatim Annex VIII rule texts and relevant guidance."
        ),
        "parameters": {
            "type": "object",
            "required": [
                "device_description",
                "intended_purpose",
                "device_type",
                "applicable_rules_hint",
            ],
            "properties": {
                "device_description": {
                    "type": "string",
                    "description": "Plain-language description of the device",
                },
                "intended_purpose": {
                    "type": "string",
                    "description": "The device's intended medical purpose",
                },
                "device_type": {
                    "type": "string",
                    "description": "Device type category (e.g. standalone software, active diagnostic)",
                },
                "applicable_rules_hint": {
                    "type": "string",
                    "description": "Comma-separated list of Annex VIII rules likely engaged (e.g. 'RULE_11, RULE_22')",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "run_comparator_engine",
        "description": (
            "Search for and rank 3-4 comparable MDR-certified devices "
            "using the multi-dimensional similarity engine. Uses web search "
            "to retrieve comparator evidence."
        ),
        "parameters": {
            "type": "object",
            "required": [
                "device_description",
                "intended_purpose",
                "device_type",
                "rule_engagement_profile",
                "consequence_severity",
                "user_type",
                "use_environment",
            ],
            "properties": {
                "device_description": {
                    "type": "string",
                    "description": "Plain-language description of the device",
                },
                "intended_purpose": {
                    "type": "string",
                    "description": "The device's intended medical purpose",
                },
                "device_type": {
                    "type": "string",
                    "description": "Device type category",
                },
                "rule_engagement_profile": {
                    "type": "string",
                    "description": "Rule engagement signature (e.g. RULE_11_FIRST_PARAGRAPH_SERIOUS_DETERIORATION)",
                },
                "consequence_severity": {
                    "type": "string",
                    "description": "Consequence-chain severity tier from the rule assessment",
                },
                "user_type": {
                    "type": "string",
                    "description": "Intended user (lay_user, healthcare_professional, etc.)",
                },
                "use_environment": {
                    "type": "string",
                    "description": "Use setting (home, clinic, hospital, etc.)",
                },
            },
            "additionalProperties": False,
        },
    },
]


def _execute_tool(
    tool_name: str,
    arguments: str,
    *,
    status_callback=None,
    audit_callback=None,
) -> str:
    """Dispatch a tool call to the appropriate nano agent."""
    args = json.loads(arguments)

    if tool_name == "run_regulatory_search":
        result = run_regulatory_search(
            device_description=args["device_description"],
            intended_purpose=args["intended_purpose"],
            device_type=args["device_type"],
            applicable_rules_hint=args["applicable_rules_hint"],
            status_callback=status_callback,
            audit_callback=audit_callback,
        )
    elif tool_name == "run_comparator_engine":
        result = run_comparator_engine(
            device_description=args["device_description"],
            intended_purpose=args["intended_purpose"],
            device_type=args["device_type"],
            rule_engagement_profile=args["rule_engagement_profile"],
            consequence_severity=args["consequence_severity"],
            user_type=args["user_type"],
            use_environment=args["use_environment"],
            status_callback=status_callback,
            audit_callback=audit_callback,
        )
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    return json.dumps(result, ensure_ascii=False)


def _record_orchestrator_call(response, audit_log: dict) -> None:
    """Append an orchestrator turn to the audit log."""
    function_calls = [item for item in response.output if item.type == "function_call"]
    builtin_calls = sorted({
        item.type for item in response.output
        if item.type in ("file_search_call", "web_search_call")
    })
    tools_invoked = sorted({tc.name for tc in function_calls}) + builtin_calls
    usage = getattr(response, "usage", None)
    audit_log["openai_calls"].append({
        "agent": "orchestrator",
        "response_id": response.id,
        "model": ORCHESTRATOR_MODEL,
        "tools_offered": [t["name"] for t in ORCHESTRATOR_TOOLS],
        "tools_invoked": tools_invoked,
        "usage": usage.model_dump() if usage and hasattr(usage, "model_dump") else None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })


def _delete_stored_responses(client: OpenAI, response_ids: list[str], audit_log: dict) -> None:
    """Delete every stored Response on OpenAI's side. Records each attempt."""
    for rid in response_ids:
        entry = {
            "response_id": rid,
            "attempted_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            client.responses.delete(rid)
            entry["status"] = "deleted"
        except Exception as exc:
            entry["status"] = "failed"
            entry["error"] = str(exc)
        audit_log["deletions"].append(entry)


def run_classification_pipeline(
    device_description: str,
    intended_purpose: str,
    device_type: str,
    user_type: str,
    use_environment: str,
    *,
    status_callback=None,
) -> dict:
    """Run the full classification pipeline and return the v4 schema JSON.

    Each invocation is single-shot: a fresh client, no carry-over from prior
    queries, and all stored OpenAI Responses created during the run are
    deleted at the end. An audit log of calls, tools and deletions is
    returned alongside the outputs.

    Returns a dict with keys:
      v4_output          – the final v4 schema JSON (dict)
      regulatory_raw     – raw regulatory nano output (dict)
      comparator_raw     – raw comparator nano output (dict)
      orchestrator_raw   – raw orchestrator final text (str)
      audit_log          – dict of calls + deletions made on OpenAI
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    audit_log: dict = {
        "session_id": str(uuid.uuid4()),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "device_parameters": {
            "device_description": device_description,
            "intended_purpose": intended_purpose,
            "device_type": device_type,
            "user_type": user_type,
            "use_environment": use_environment,
        },
        "openai_calls": [],
        "deletions": [],
        "completed_at": None,
    }

    def _nano_audit(entry: dict) -> None:
        entry = dict(entry)
        entry["recorded_at"] = datetime.now(timezone.utc).isoformat()
        audit_log["openai_calls"].append(entry)

    v4_schema_text = _V4_SCHEMA_PATH.read_text()

    user_message = f"""Classify the following medical device under MDR Annex VIII.

DEVICE PARAMETERS
=================
Device description: {device_description}
Intended purpose: {intended_purpose}
Device type: {device_type}
Intended user: {user_type}
Use environment: {use_environment}

INSTRUCTIONS
============
1. First call run_regulatory_search to retrieve Annex VIII rule texts
   and relevant guidance.
2. Perform your rule-by-rule assessment using the retrieved texts.
3. Then call run_comparator_engine to find comparable devices.
4. Compose the final output as JSON conforming to this schema:

{v4_schema_text}

Return ONLY the JSON. No markdown fences."""

    if status_callback:
        status_callback("Orchestrator: analysing device parameters...")

    nano_outputs = {"regulatory_raw": None, "comparator_raw": None}

    response = client.responses.create(
        model=ORCHESTRATOR_MODEL,
        instructions=_SYSTEM,
        input=[{"role": "user", "content": user_message}],
        tools=ORCHESTRATOR_TOOLS,
        reasoning={"effort": "medium"},
    )
    _record_orchestrator_call(response, audit_log)

    max_rounds = 6
    for _ in range(max_rounds):
        tool_calls = [
            item for item in response.output if item.type == "function_call"
        ]
        if not tool_calls:
            break

        tool_results_input = []
        for tc in tool_calls:
            if status_callback:
                status_callback(f"Orchestrator: calling {tc.name}...")

            tool_output = _execute_tool(
                tc.name, tc.arguments,
                status_callback=status_callback,
                audit_callback=_nano_audit,
            )

            if tc.name == "run_regulatory_search":
                nano_outputs["regulatory_raw"] = json.loads(tool_output)
            elif tc.name == "run_comparator_engine":
                nano_outputs["comparator_raw"] = json.loads(tool_output)

            tool_results_input.append({
                "type": "function_call",
                "name": tc.name,
                "call_id": tc.call_id,
                "arguments": tc.arguments,
            })
            tool_results_input.append(
                {
                    "type": "function_call_output",
                    "call_id": tc.call_id,
                    "output": tool_output,
                }
            )

        if status_callback:
            status_callback("Orchestrator: composing classification output...")

        response = client.responses.create(
            model=ORCHESTRATOR_MODEL,
            instructions=_SYSTEM,
            input=tool_results_input,
            tools=ORCHESTRATOR_TOOLS,
            previous_response_id=response.id,
            reasoning={"effort": "medium"},
        )
        _record_orchestrator_call(response, audit_log)

    try:
        raw_text = response.output_text
    except Exception:
        raw_text = ""

    if raw_text:
        try:
            v4_output = json.loads(raw_text)
        except json.JSONDecodeError:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n", 1)
                cleaned = lines[1] if len(lines) > 1 else ""
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            try:
                v4_output = json.loads(cleaned.strip())
            except json.JSONDecodeError:
                v4_output = {"error": "Failed to parse orchestrator output", "raw": raw_text[:3000]}
    else:
        v4_output = {"error": "Orchestrator produced no text output after tool calls"}

    if status_callback:
        status_callback("Cleanup: deleting stored OpenAI responses...")

    response_ids = [call["response_id"] for call in audit_log["openai_calls"]]
    _delete_stored_responses(client, response_ids, audit_log)

    audit_log["completed_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "v4_output": v4_output,
        "regulatory_raw": nano_outputs["regulatory_raw"],
        "comparator_raw": nano_outputs["comparator_raw"],
        "orchestrator_raw": raw_text,
        "audit_log": audit_log,
    }
