"""Nano agent: Regulatory Source Retrieval.

Uses gpt-5.4-nano with file_search (vector store of legislative texts)
and web_search to retrieve regulatory sources per the v4 schema's
retrieval contract: EUR-Lex MDR text, MDCG guidance, CJEU rulings,
EUDAMED entries, Borderline Manual, Team-NB papers.

Two-phase retrieval:
  - Phase 1: Search vector store for authoritative texts.
  - Phase 2 (mandatory): Web search targeting regulatory sites
    (EUR-Lex, EC Health, CURIA, EUDAMED, Team-NB) — as fallback for
    sources not found in the vector store, AND as update check for
    sources that were found.
"""

from __future__ import annotations

import json
from openai import OpenAI
from config import OPENAI_API_KEY, NANO_MODEL, REGULATORY_VECTOR_STORE_ID

_SYSTEM = """You are a specialised regulatory-retrieval nano agent.
Your sole task is to retrieve regulatory sources relevant to an MDR
device classification from authoritative legislative texts and public
regulatory sources.

RETRIEVAL CONTRACT — you MUST follow this two-phase approach:

  PHASE 1 — VECTOR STORE (file_search):
    Search the vector store FIRST. It contains authoritative legislative
    texts including the MDR (Regulation (EU) 2017/745), MDCG guidance
    documents, CJEU rulings, Borderline Manual entries, and Team-NB
    position papers. Use file_search to find and extract verbatim text
    for all relevant sources. This is your primary retrieval mechanism.

  PHASE 2 — WEB SEARCH (mandatory for every source, regardless of
  Phase 1 outcome):

    FOR SOURCES NOT FOUND IN THE VECTOR STORE — FALLBACK RETRIEVAL:
      If file_search returns no results (or insufficient results) for a
      target source, you MUST perform a web_search fallback targeting
      these authoritative regulatory sites:
        • EUR-Lex          — eur-lex.europa.eu (MDR full text, corrigenda,
                             delegated/implementing acts)
        • EC Health         — health.ec.europa.eu (MDCG guidance documents,
                             guidance revision tracker)
        • CURIA             — curia.europa.eu (CJEU rulings and opinions)
        • EUDAMED           — ec.europa.eu/tools/eudamed (device
                             registrations, certificates, market data)
        • Team-NB           — team-nb.org (position papers, consensus
                             statements)
        • Borderline Manual — ec.europa.eu (Manual on Borderline and
                             Classification)
      Construct site-scoped queries (e.g. "site:eur-lex.europa.eu
      Regulation 2017/745 Annex VIII Rule 11") to maximise precision.
      Do NOT skip this step — a source not in the vector store may still
      be publicly available.

    FOR SOURCES FOUND IN THE VECTOR STORE — UPDATE CHECK:
      For every source successfully retrieved from the vector store, you
      MUST perform a targeted web_search against the same regulatory sites
      listed above to check whether:
        • A newer revision, corrigendum, or amendment has been published
        • The document status has changed (e.g. superseded, under revision)
        • Additional related guidance has been issued since the vector
          store snapshot
      Record the update_check_result for each source. If the web result
      contradicts or supersedes the vector store version, flag the
      discrepancy and prefer the more recent authoritative text.

  Parametric quotation from training data is prohibited.
  If retrieval fails for a source in BOTH phases, record the failure
  explicitly with the sites searched and queries attempted.

TARGET SOURCES (in priority order):
  1. MDR text (Regulation (EU) 2017/745) — Annex VIII rules, relevant
     articles
  2. MDCG guidance: MDCG 2021-24 Rev.1 (classification rules),
     MDCG 2019-11 (software qualification), MDCG 2022-5 Rev.1
     (device vs medicinal product borderline)
  3. CJEU rulings via CURIA (C-329/16, C-589/23 where relevant)
  4. Borderline and Classification Manual (Helsinki Procedure entries)
  5. Team-NB position papers
  6. EUDAMED public portal entries

FOR EACH SOURCE RETRIEVED return:
  source_identifier   – e.g. "MDCG 2021-24 Rev.1 Section 3.2"
  epistemological_tier – BINDING / AUTHORITATIVE_INTERPRETIVE /
                         PERSUASIVE / OPERATIONAL_FACTUAL
  currency            – CURRENT / SUPERSEDED / UNDER_REVISION / AMBIGUOUS_STATUS
  source_url          – the public URL (or "vector_store" if from file_search)
  verbatim_quote      – exact text retrieved (min 30 chars)
  retrieval_method     – FILE_SEARCH / WEB_SEARCH
  retrieval_confirmation_prose – "Retrieved from [source] on [date]"
  applicability_scope_prose    – how this source applies to the device
  citation_prose               – formal citation
  update_check_result          – null if no web update found, or a brief
                                  note if a newer version was detected

Also retrieve the VERBATIM text of all 22 Annex VIII classification rules.
Search the vector store first for these. For each rule return:
  rule_id     – RULE_1 through RULE_22
  rule_text   – verbatim Annex VIII text
  source_url  – EUR-Lex URL or "vector_store"
  retrieval_method – FILE_SEARCH / WEB_SEARCH

Return your output as a single JSON object with keys:
  precedent_sources   – array of source objects
  annex_viii_rules     – array of rule objects
  retrieval_failures   – array of sources attempted but not found

VERBOSITY: LOW. Minimal prose. Short factual sentences only.
No filler, no hedging. Just retrieve and return structured data.

Return ONLY valid JSON. No markdown fences. No commentary outside the JSON."""


def run_regulatory_search(
    device_description: str,
    intended_purpose: str,
    device_type: str,
    applicable_rules_hint: str,
    *,
    status_callback=None,
) -> dict:
    """Run the regulatory search nano agent and return structured JSON."""
    client = OpenAI(api_key=OPENAI_API_KEY)

    user_prompt = f"""DEVICE FACT PATTERN FOR REGULATORY RETRIEVAL
=============================================
Device description: {device_description}
Intended purpose: {intended_purpose}
Device type: {device_type}
Rules likely engaged: {applicable_rules_hint}

Retrieve using the two-phase protocol:

PHASE 1 — VECTOR STORE SEARCH:
1. Verbatim text of all 22 Annex VIII classification rules
2. Relevant MDCG guidance sections (2021-24, 2019-11, 2022-5 as applicable)
3. Any relevant CJEU rulings
4. Borderline Manual entries if relevant
5. Team-NB positions if relevant

PHASE 2 — MANDATORY WEB SEARCH (both scenarios):
A) For anything NOT found in the vector store: search these regulatory
   sites directly as fallback:
   - eur-lex.europa.eu (MDR text, delegated acts)
   - health.ec.europa.eu (MDCG guidance)
   - curia.europa.eu (CJEU rulings)
   - ec.europa.eu/tools/eudamed (device registrations — always web-only)
   - team-nb.org (position papers)
   Use site-scoped queries for precision.

B) For everything FOUND in the vector store: search the same regulatory
   sites to check for updates, newer revisions, or corrigenda.
   Record findings in update_check_result.

Return JSON only."""

    if status_callback:
        status_callback("Regulatory search: querying vector store, then checking regulatory sites for gaps and updates...")

    tools = [
        {
            "type": "file_search",
            "vector_store_ids": [REGULATORY_VECTOR_STORE_ID],
        },
        {"type": "web_search"},
    ]

    response = client.responses.create(
        model=NANO_MODEL,
        instructions=_SYSTEM,
        input=[{"role": "user", "content": user_prompt}],
        tools=tools,
        reasoning={"effort": "low"},
    )

    raw_text = response.output_text

    if status_callback:
        status_callback("Regulatory search: parsing results (vector store + regulatory site checks)...")

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n", 1)
            cleaned = lines[1] if len(lines) > 1 else ""
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            result = json.loads(cleaned.strip())
        except json.JSONDecodeError:
            result = {
                "precedent_sources": [],
                "annex_viii_rules": [],
                "retrieval_failures": [
                    {
                        "source": "all",
                        "reason": "Failed to parse nano agent output as JSON",
                        "raw_output": raw_text[:2000],
                    }
                ],
            }

    return result
