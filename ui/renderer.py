"""Render the v4 schema JSON output as a human-readable regulatory note."""

from __future__ import annotations
import streamlit as st

from ui.download import generate_bundle_zip


def render_classification_result(result: dict, device_params: dict | None = None) -> None:
    """Render the full pipeline result in the Streamlit main area."""
    v4 = result.get("v4_output", {})

    if "error" in v4:
        st.error(f"Classification failed: {v4['error']}")
        if "raw" in v4:
            with st.expander("Raw orchestrator output"):
                st.code(v4["raw"], language="text")
        return

    _render_download_button(result, device_params)
    _render_header(v4)
    _render_rationale(v4)
    _render_rule_assessment(v4)
    _render_applicable_rules(v4)
    _render_comparable_devices(v4)
    _render_uncertainties(v4)
    _render_validation(v4)
    _render_audit_log(result)
    _render_raw_json_sections(result)


def _render_download_button(result: dict, device_params: dict | None) -> None:
    """Single button that bundles the Word doc, JSON packages and audit log."""
    params = device_params or {}
    try:
        zip_bytes, filename = generate_bundle_zip(result, params)
    except Exception as exc:
        st.warning(f"Could not prepare download bundle: {exc}")
        return

    st.download_button(
        label="Download session bundle (.zip)",
        data=zip_bytes,
        file_name=filename,
        mime="application/zip",
        type="primary",
        help=(
            "Bundle includes: classification Word document, full session JSON, "
            "individual JSON packages (v4 output, regulatory search, comparator "
            "engine) and the audit log of OpenAI calls and deletions."
        ),
        use_container_width=True,
    )


def _render_audit_log(result: dict) -> None:
    audit = result.get("audit_log")
    if not audit:
        return
    with st.expander("Audit log (OpenAI calls and deletions)"):
        calls = audit.get("openai_calls", [])
        dels = audit.get("deletions", [])
        st.markdown(
            f"**Session:** `{audit.get('session_id', '—')}`  \n"
            f"**Started:** {audit.get('started_at', '—')}  \n"
            f"**Completed:** {audit.get('completed_at', '—')}  \n"
            f"**Calls:** {len(calls)}   **Deletions:** {len(dels)}"
        )
        if calls:
            st.markdown("**Calls**")
            for c in calls:
                tools = ", ".join(c.get("tools_invoked") or []) or "—"
                st.markdown(
                    f"- `{c.get('agent', '?')}` · "
                    f"`{c.get('response_id', '—')}` · "
                    f"model `{c.get('model', '—')}` · tools: {tools}"
                )
        if dels:
            st.markdown("**Deletions**")
            for d in dels:
                st.markdown(
                    f"- `{d.get('response_id', '—')}` — {d.get('status', '—')}"
                    + (f" ({d.get('error')})" if d.get("error") else "")
                )


def _render_header(v4: dict) -> None:
    s1 = v4.get("section_1_final_mdr_device_classification", {})
    s2 = v4.get("section_2_primary_mdr_classification_rule", {})

    provisional_class = s1.get("provisional_class", "—")
    class_colors = {"I": "green", "IIa": "blue", "IIb": "orange", "III": "red"}
    color = class_colors.get(provisional_class, "gray")

    st.markdown(f"### Provisional Classification: :{color}[Class {provisional_class}]")
    st.info(s1.get("single_sentence_statement", ""))
    st.caption("This classification is provisional and requires human review under MDR Article 51.")

    st.markdown(f"**Primary rule:** {s2.get('rule', '—')} — {s2.get('sub_clause_description', '—')}")
    st.markdown(s2.get("single_paragraph_statement", ""))


def _render_rationale(v4: dict) -> None:
    s3 = v4.get("section_3_classification_rationale", {})
    if not s3:
        return

    with st.expander("Classification Rationale", expanded=True):
        st.markdown("**Controlling logic**")
        st.markdown(s3.get("controlling_logic_prose", ""))

        verbatim = s3.get("annex_viii_text_verbatim", {})
        if verbatim:
            st.markdown("**Annex VIII text (verbatim)**")
            st.caption(f"Source: {verbatim.get('source_url', '—')}")
            st.markdown(f"> {verbatim.get('text', '')}")

        st.markdown("**Consequence assessment**")
        st.markdown(s3.get("consequence_assessment_prose", ""))

        rejected = s3.get("inadmissible_inputs_rejected", [])
        if rejected:
            st.markdown("**Inadmissible inputs rejected**")
            for inp in rejected:
                st.markdown(
                    f"- **{inp.get('input_type', '')}**: "
                    f"_{inp.get('input_value_quoted', '')}_  \n"
                    f"  {inp.get('rejection_prose', '')}"
                )


def _render_rule_assessment(v4: dict) -> None:
    s6 = v4.get("section_6_rule_by_rule_assessment", [])
    if not s6:
        return

    with st.expander("Rule-by-Rule Assessment (22 rules)"):
        for rule_item in s6:
            rule_id = rule_item.get("rule", "")
            applicability = rule_item.get("applicability", "")
            resulting_class = rule_item.get("resulting_class_if_applicable")

            if applicability == "APPLICABLE":
                icon = "+"
                label = f"**{rule_id}** — APPLICABLE (Class {resulting_class})"
            elif applicability == "INDETERMINATE":
                icon = "?"
                label = f"**{rule_id}** — INDETERMINATE"
            else:
                icon = "—"
                label = f"{rule_id} — not applicable"

            st.markdown(f"{icon} {label}")
            if applicability != "NOT_APPLICABLE":
                st.markdown(f"  {rule_item.get('assessment_prose', '')}")


def _render_applicable_rules(v4: dict) -> None:
    s7 = v4.get("section_7_applicable_rules", [])
    s8 = v4.get("section_8_excluded_rules", {})

    if s7:
        with st.expander("Applicable Rules Summary"):
            st.markdown(", ".join(f"**{r}**" for r in s7))
            if s8:
                st.markdown("**Excluded rules reasoning:**")
                st.markdown(s8.get("excluded_rules_prose", ""))


def _render_comparable_devices(v4: dict) -> None:
    s10 = v4.get("section_10_validation_against_mdr_annex_viii_and_mdcg_2021_24", {})
    comparable = s10.get("comparable_devices_assessed", [])
    competing = s10.get("competing_precedents_acknowledged", [])
    unavailable = s10.get("unavailable_comparators_acknowledged", [])

    with st.expander("Comparable Devices Assessed", expanded=True):
        if not comparable:
            st.warning("No comparable devices were retrieved.")
        else:
            for i, dev in enumerate(comparable, 1):
                st.markdown(f"#### {i}. {dev.get('device_identifier', 'Unknown')}")

                cols = st.columns(3)
                cols[0].metric("Similarity", f"{dev.get('similarity_score_final', 0):.2f}")
                cols[1].metric("Quality", dev.get("match_quality_rating", "—"))
                cols[2].metric("Status", dev.get("regulatory_status", "—")[:30])

                st.markdown(f"**Why this comparator scored highly:** {dev.get('precedent_weight_reasoning_prose', '')}")
                st.markdown(f"**What transfers:** {dev.get('transfers_reasoning_to_present_prose', '')}")
                st.markdown(f"**Limits of transfer:** {dev.get('limits_of_transfer_prose', '')}")

                purpose = dev.get("intended_purpose_verbatim_quote", "")
                if purpose:
                    st.markdown(f"> _{purpose}_")
                    st.caption(f"Source: {dev.get('intended_purpose_quote_url', '—')}")

                if i < len(comparable):
                    st.divider()

        if competing:
            st.markdown("---")
            st.markdown("**Competing precedents (different classification direction)**")
            for cp in competing:
                st.warning(
                    f"**{cp.get('competing_device_identifier', '')}** — "
                    f"Class {cp.get('competing_classification_reached', '?')}\n\n"
                    f"{cp.get('competing_reasoning_prose', '')}\n\n"
                    f"_Why not top match:_ {cp.get('why_not_top_match_prose', '')}"
                )

        if unavailable:
            st.markdown("---")
            st.markdown("**Unavailable comparators**")
            for uc in unavailable:
                st.caption(
                    f"{uc.get('comparator_identifier', '')} — "
                    f"{uc.get('exclusion_reason', '')}: "
                    f"{uc.get('exclusion_acknowledgement_prose', '')}"
                )

        critique = s10.get("source_hierarchy_critique_prose", "")
        if critique:
            st.markdown("**Source hierarchy critique**")
            st.markdown(critique)


def _render_uncertainties(v4: dict) -> None:
    s9 = v4.get("section_9_rule_conflict_and_precedence_assessment", {})
    uncertainties = s9.get("interpretive_uncertainties_flagged", [])

    if not uncertainties:
        return

    with st.expander("Interpretive Uncertainties", expanded=True):
        st.markdown(s9.get("precedence_prose", ""))

        for unc in uncertainties:
            load_bearing = unc.get("load_bearing_to_classification", False)
            icon = "!!!" if load_bearing else "..."
            st.markdown(
                f"**{icon} {unc.get('uncertainty_type', '')}** "
                f"{'(load-bearing)' if load_bearing else ''}"
            )
            st.markdown(f"_Provisional position:_ {unc.get('substrate_provisional_position_prose', '')}")
            st.markdown(f"_Human deliberation needed:_ {unc.get('human_deliberation_rationale_prose', '')}")


def _render_validation(v4: dict) -> None:
    s10 = v4.get("section_10_validation_against_mdr_annex_viii_and_mdcg_2021_24", {})
    s11 = v4.get("section_11_validation_status", {})
    checks = s10.get("validation_checks", {})

    with st.expander("Validation"):
        if checks:
            for check_name, passed in checks.items():
                icon = "OK" if passed else "FAIL"
                st.markdown(f"- {icon} {check_name.replace('_', ' ')}")

        st.markdown(s10.get("validation_summary_prose", ""))

        status = s11.get("status", "")
        closing = s11.get("closing_statement_prose", "")
        st.markdown(f"**Status:** {status}")
        st.markdown(closing)

        missing = s11.get("missing_parameters_if_insufficient", [])
        if missing:
            st.markdown("**Missing parameters:**")
            for m in missing:
                st.markdown(
                    f"- **{m.get('parameter_name', '')}** ({m.get('reason', '')}): "
                    f"{m.get('clarification_needed_prose', '')}"
                )


def _render_raw_json_sections(result: dict) -> None:
    """Collapsible raw JSON from each agent."""
    st.markdown("---")
    st.markdown("### Raw Agent Outputs")

    with st.expander("Orchestrator Output (v4 schema JSON)"):
        st.json(result.get("v4_output", {}))

    with st.expander("Regulatory Search Nano Output"):
        reg = result.get("regulatory_raw")
        if reg:
            st.json(reg)
        else:
            st.caption("No regulatory search output recorded.")

    with st.expander("Comparator Engine Nano Output"):
        comp = result.get("comparator_raw")
        if comp:
            st.json(comp)
        else:
            st.caption("No comparator engine output recorded.")
