"""Sidebar form for device parameter input.

Structured per MDR Annex VIII so every field maps back to the rule(s) it
drives. Conditional gating keeps each section relevant: sub-questions
appear only when the parent answer would make them load-bearing.
"""

from __future__ import annotations
import streamlit as st


PRINCIPAL_MODE = [
    "Mechanical / physical",
    "Electrical / electronic",
    "Software / algorithm",
    "Pharmacological",
    "Immunological",
    "Metabolic",
    "Combination (device + ancillary medicinal substance)",
    "Unsure / borderline",
]

REUSABILITY = [
    "Single-use",
    "Reusable",
    "Reusable surgical instrument",
]

STERILE_STATE = [
    "Supplied non-sterile",
    "Supplied sterile",
    "Sterilised before use",
]

INVASIVENESS_CATEGORY = [
    "Non-invasive",
    "Invasive via body orifice",
    "Surgically invasive (transient or short-term)",
    "Surgically invasive long-term or implantable",
    "Implantable",
]

NON_INVASIVE_CONTACT = [
    "No body contact",
    "Intact skin only",
    "Injured skin or mucous membrane",
    "Channels or stores blood, fluids, cells or gases for infusion or administration",
    "Modifies the biological or chemical composition of blood or body liquids",
]

ANATOMICAL_SITES = [
    "Skin",
    "Body orifice",
    "Eye surface",
    "GI tract",
    "Airway or respiratory",
    "Heart",
    "Central circulatory system",
    "Central nervous system",
    "Other",
]

DURATION = [
    "Transient (under 60 minutes)",
    "Short-term (60 minutes to 30 days)",
    "Long-term (over 30 days)",
]

ACTIVE_FUNCTIONS = [
    "Administers or exchanges energy for therapy",
    "Supplies or images energy for diagnosis",
    "Monitors vital physiological parameters",
    "Emits ionising radiation",
    "Controls or influences another active device",
    "Administers or removes medicines, body liquids or other substances",
]

DECISION_SIGNIFICANCE = [
    "Other diagnostic or therapeutic decisions (Class IIa)",
    "May cause serious deterioration or surgical intervention (Class IIb)",
    "May cause death or irreversible deterioration (Class III)",
]

MONITORING_ROLE = [
    "Does not monitor",
    "Monitors other physiological parameters (Class IIa)",
    "Monitors vital parameters where variation could cause immediate danger (Class IIb)",
]

NA = "N/A"

R14_MED_OPTIONS = [
    NA,
    "Triggered — medicinal substance with ancillary action (Class III)",
]

R14_BLOOD_OPTIONS = [
    NA,
    "Triggered — human blood derivative (Class III)",
]

R15_OPTIONS = [
    NA,
    "Barrier, oral or other non-invasive (Class IIb)",
    "Implantable or long-term invasive (Class III)",
]

R16_OPTIONS = [
    NA,
    "Disinfects non-invasive medical devices (Class IIa)",
    "Disinfects invasive medical devices (Class IIb)",
    "Disinfects, cleans, rinses or hydrates contact lenses (Class IIb)",
]

R17_OPTIONS = [
    NA,
    "Triggered — records X-ray diagnostic images (Class IIa)",
]

R18_OPTIONS = [
    NA,
    "Non-viable human-origin tissue or derivative (Class III)",
    "Animal-origin tissue, intact-skin contact only (Class IIa)",
    "Animal-origin tissue, other contact (Class III)",
]

R19_OPTIONS = [
    NA,
    "Negligible internal exposure potential (Class IIa)",
    "Low internal exposure potential (Class IIb)",
    "Medium or high internal exposure potential (Class III)",
]

R20_OPTIONS = [
    NA,
    "Standard mode of action (Class IIa)",
    "Essential impact on efficacy/safety, or life-threatening (Class IIb)",
]

R21_OPTIONS = [
    NA,
    "Local action on skin or nasal/oral cavity (Class IIa)",
    "Local action elsewhere in the body (Class IIb)",
    "Systemically absorbed to achieve intended purpose (Class III)",
    "Acts in stomach or lower GI and is systemically absorbed (Class III)",
]

USER_TYPES = [
    "Lay user",
    "Healthcare professional",
    "Both",
]

USE_ENVIRONMENTS = [
    "Home / lifestyle",
    "Home (clinical, supervised)",
    "Primary care clinic",
    "Hospital ward",
    "Intensive care unit",
    "Emergency department",
    "Operating theatre",
    "Ambulance / field",
]


def _toggle(
    label: str,
    *,
    help: str | None = None,
    default: bool = False,
    disabled: bool = False,
) -> str:
    """Yes/No toggle that returns a stable string for the audit log."""
    return "Yes" if st.toggle(label, value=default, help=help, disabled=disabled) else "No"


def render_sidebar() -> dict | None:
    """Render the structured sidebar form. Returns device params on submit."""
    with st.sidebar:
        st.header("Device classification")
        st.caption(
            "Answer what you know. Sub-questions appear only when they "
            "change the rule outcome — skip a section if it doesn't apply."
        )

        with st.form("device_form", clear_on_submit=False):

            # ── 1. Identity and purpose ───────────────────────────
            st.subheader("1. Identity and purpose")
            device_description = st.text_area(
                "Device description",
                height=100,
                placeholder="What the device is, in plain language.",
            )
            intended_purpose = st.text_area(
                "Intended purpose *",
                height=100,
                placeholder="The medical claim — what the device does for the patient.",
                help=(
                    "State the claim, not the mechanism. Every rule reads "
                    "from this field."
                ),
            )
            principal_mode_of_action = st.selectbox(
                "Principal mode of action *",
                PRINCIPAL_MODE,
                index=0,
                help=(
                    "Qualification gate (MDCG 2022-5 + Article 2(1) MDR). "
                    "If the principal action is pharmacological, immunological "
                    "or metabolic, the product is likely a medicinal product "
                    "under Directive 2001/83/EC and falls outside MDR scope. "
                    "Annex VIII output will be presented as conditional."
                ),
            )
            reusability = st.selectbox("Reusability", REUSABILITY, index=0)
            sterile_state = st.selectbox("Sterile state", STERILE_STATE, index=0)
            measuring_function = _toggle(
                "Has a measuring function",
                help='Triggers the Class Im designation when "Yes".',
                default=False,
            )

            # ── 2. Body contact and invasiveness ──────────────────
            st.subheader("2. Body contact")
            invasiveness_category = st.selectbox(
                "Invasiveness", INVASIVENESS_CATEGORY, index=0
            )
            non_invasive_contact_type = ""
            if invasiveness_category == "Non-invasive":
                non_invasive_contact_type = st.selectbox(
                    "Contact type", NON_INVASIVE_CONTACT, index=0
                )
            anatomical_contact_sites = st.multiselect(
                "Anatomical contact site(s)",
                ANATOMICAL_SITES,
                help=(
                    "Heart, central circulatory or central nervous system "
                    "escalate to Class III."
                ),
            )
            connected_to_active_device = _toggle(
                "Connected to a separate active device",
                help="A passive device connected to active equipment may escalate under Rule 8.",
            )

            # ── 3. Duration of use ────────────────────────────────
            st.subheader("3. Duration of use")
            duration_of_use = st.selectbox(
                "Continuous use",
                DURATION,
                index=0,
                help=(
                    "Interrupted use of the same device counts cumulatively "
                    "toward the duration bucket."
                ),
            )

            # ── 4. Active device function (gated) ─────────────────
            st.subheader("4. Active device function")
            is_active_device = _toggle(
                "This is an active device",
                help=(
                    "Active = runs on energy other than that generated by "
                    "the human body or by gravity. Rules 9, 10, 12, 13 and "
                    "22 only apply if Yes."
                ),
            )
            active_functions: list[str] = []
            hazardous_energy_administration = "No"
            monitors_vital_immediate_danger = "No"
            integrated_closed_loop_diagnostic = "No"
            if is_active_device == "Yes":
                active_functions = st.multiselect(
                    "What does it do (one or more)?", ACTIVE_FUNCTIONS
                )
                hazardous_energy_administration = _toggle(
                    "Administers potentially hazardous energy",
                    help="Rule 9 escalation to Class IIb.",
                )
                monitors_vital_immediate_danger = _toggle(
                    "Monitors vital signs where failure could be immediately dangerous",
                    help="Rule 10 escalation to Class IIb.",
                )
                integrated_closed_loop_diagnostic = _toggle(
                    "Integrated closed-loop diagnostic that determines patient management",
                    help="Rule 22 — Class III.",
                )

            # ── 5. Software (gated) ───────────────────────────────
            st.subheader("5. Software (MDSW)")
            is_mdsw = _toggle(
                "Standalone medical device software (MDSW)",
                help="Gates Rule 11. Skip if the device is not software.",
            )
            info_drives_decisions = "No"
            decision_significance = ""
            monitoring_role = ""
            drives_hardware_device = "No"
            if is_mdsw == "Yes":
                info_drives_decisions = _toggle(
                    "Information drives a diagnostic or therapeutic decision",
                    help='If "No", Rule 11 places the software at Class I.',
                )
                if info_drives_decisions == "Yes":
                    decision_significance = st.selectbox(
                        "Impact of that decision",
                        DECISION_SIGNIFICANCE,
                        index=0,
                        help="Picks the Rule 11 class.",
                    )
                monitoring_role = st.selectbox(
                    "Monitoring role", MONITORING_ROLE, index=0
                )
                drives_hardware_device = _toggle(
                    "Drives or controls a hardware device",
                    help="If yes, the software inherits the host device's pathway.",
                )

            # ── 6. Special-rule triggers ──────────────────────────
            st.subheader("6. Special-rule triggers")
            st.caption(
                "Leave each row at **N/A** when the rule doesn't apply. "
                "Picking any other option both triggers the rule and selects "
                "the class in one step."
            )

            rule_14_medicinal_substance = st.selectbox(
                "Rule 14 — incorporates a medicinal substance with ancillary action",
                R14_MED_OPTIONS,
                index=0,
            )
            rule_14_blood_derivative = st.selectbox(
                "Rule 14 — incorporates a human blood derivative",
                R14_BLOOD_OPTIONS,
                index=0,
            )
            rule_15_choice = st.selectbox(
                "Rule 15 — contraception or prevention of sexually transmitted infection",
                R15_OPTIONS,
                index=0,
                help="Implantable or long-term invasive contraceptives → III; others → IIb.",
            )
            rule_16_choice = st.selectbox(
                "Rule 16 — disinfects, cleans, sterilises or hydrates medical devices",
                R16_OPTIONS,
                index=0,
                help="Invasive devices or contact lenses → IIb; non-invasive → IIa.",
            )
            rule_17_xray_images = st.selectbox(
                "Rule 17 — records diagnostic images generated by X-ray",
                R17_OPTIONS,
                index=0,
            )
            rule_18_non_viable_tissue = st.selectbox(
                "Rule 18 — incorporates non-viable human or animal tissue",
                R18_OPTIONS,
                index=0,
            )
            rule_19_choice = st.selectbox(
                "Rule 19 — incorporates or consists of nanomaterial",
                R19_OPTIONS,
                index=0,
                help="Negligible → IIa, Low → IIb, Medium or high → III.",
            )
            rule_20_choice = st.selectbox(
                "Rule 20 — administers medicinal products by inhalation via a body orifice",
                R20_OPTIONS,
                index=0,
                help="Essential impact on efficacy/safety or life-threatening → IIb; otherwise IIa.",
            )
            rule_21_choice = st.selectbox(
                "Rule 21 — composed of substances via body orifice or applied to the skin",
                R21_OPTIONS,
                index=0,
                help="Mode of action picks the Rule 21 class.",
            )

            # ── 7. Use context ────────────────────────────────────
            st.subheader("7. Use context")
            user_type = st.selectbox("Intended user", USER_TYPES, index=1)
            use_environment = st.selectbox(
                "Use environment", USE_ENVIRONMENTS, index=3
            )
            multiple_intended_uses = st.text_area(
                "Most critical intended use",
                height=70,
                placeholder=(
                    "Optional — if the device has several intended uses, "
                    "name the highest-risk one."
                ),
                help="Implementing rules classify on the highest-risk intended use.",
            )

            st.divider()
            submitted = st.form_submit_button(
                "Classify device", type="primary", use_container_width=True
            )

        if not submitted:
            return None

        if not device_description.strip():
            st.error("Please provide a device description.")
            return None
        if not intended_purpose.strip():
            st.error("Please provide the intended purpose (medical claim).")
            return None

        return {
            # Section 1
            "device_description": device_description.strip(),
            "intended_purpose": intended_purpose.strip(),
            "principal_mode_of_action": principal_mode_of_action,
            "reusability": reusability,
            "sterile_state": sterile_state,
            "measuring_function": measuring_function,
            # Section 2
            "invasiveness_category": invasiveness_category,
            "non_invasive_contact_type": non_invasive_contact_type,
            "anatomical_contact_sites": anatomical_contact_sites,
            "connected_to_active_device": connected_to_active_device,
            # Section 3
            "duration_of_use": duration_of_use,
            # Section 4
            "is_active_device": is_active_device,
            "active_functions": active_functions,
            "hazardous_energy_administration": hazardous_energy_administration,
            "monitors_vital_immediate_danger": monitors_vital_immediate_danger,
            "integrated_closed_loop_diagnostic": integrated_closed_loop_diagnostic,
            # Section 5
            "is_mdsw": is_mdsw,
            "info_drives_decisions": info_drives_decisions,
            "decision_significance": decision_significance,
            "monitoring_role": monitoring_role,
            "drives_hardware_device": drives_hardware_device,
            # Section 6 (each value is "N/A" when the rule does not apply,
            # otherwise the descriptive option with class annotation)
            "rule_14_medicinal_substance": rule_14_medicinal_substance,
            "rule_14_blood_derivative": rule_14_blood_derivative,
            "rule_15_choice": rule_15_choice,
            "rule_16_choice": rule_16_choice,
            "rule_17_xray_images": rule_17_xray_images,
            "rule_18_non_viable_tissue": rule_18_non_viable_tissue,
            "rule_19_choice": rule_19_choice,
            "rule_20_choice": rule_20_choice,
            "rule_21_choice": rule_21_choice,
            # Section 7
            "user_type": user_type,
            "use_environment": use_environment,
            "multiple_intended_uses": multiple_intended_uses.strip(),
        }
