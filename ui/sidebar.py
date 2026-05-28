"""Sidebar form for device parameter input.

Structured per MDR Annex VIII implementing rules so every field can be
mapped back to the rule(s) it drives.
"""

from __future__ import annotations
import streamlit as st


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

YN = ["No", "Yes"]

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
    "Informs without driving decisions (Class I)",
    "Other diagnostic or therapeutic decisions (Class IIa)",
    "May cause serious deterioration or surgical intervention (Class IIb)",
    "May cause death or irreversible deterioration (Class III)",
]

MONITORING_ROLE = [
    "Does not monitor",
    "Monitors other physiological parameters (Class IIa)",
    "Monitors vital parameters where variation could cause immediate danger (Class IIb)",
]

NANO_EXPOSURE = [
    "Negligible",
    "Low",
    "Medium or high",
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


def _yn(label: str, *, help: str | None = None, default: str = "No") -> str:
    return st.radio(label, YN, index=YN.index(default), horizontal=True, help=help)


def render_sidebar() -> dict | None:
    """Render the structured sidebar form. Returns device params on submit."""
    with st.sidebar:
        st.header("Device Parameters")

        with st.form("device_form", clear_on_submit=False):

            # ── 1. Identity and purpose ───────────────────────────
            st.subheader("1. Identity and purpose")
            device_description = st.text_area(
                "Device description",
                height=110,
                placeholder="Describe the medical device in plain language...",
            )
            intended_purpose = st.text_area(
                "Intended purpose *",
                height=100,
                placeholder="State the medical claim, not the mechanism.",
                help=(
                    "This is the pivot for every rule. Describe the medical "
                    "claim (what the device is intended to do for the patient), "
                    "not how it works."
                ),
            )
            reusability = st.selectbox("Reusability", REUSABILITY)
            sterile_state = st.selectbox("Sterile state", STERILE_STATE)
            measuring_function = _yn(
                "Measuring function",
                help='"Yes" triggers the Class Im designation.',
            )

            # ── 2. Invasiveness and body contact ──────────────────
            st.subheader("2. Invasiveness and body contact")
            invasiveness_category = st.selectbox(
                "Invasiveness category", INVASIVENESS_CATEGORY
            )
            non_invasive_contact_type = ""
            if invasiveness_category == "Non-invasive":
                non_invasive_contact_type = st.selectbox(
                    "Non-invasive contact type", NON_INVASIVE_CONTACT
                )
            anatomical_contact_sites = st.multiselect(
                "Anatomical contact site(s)",
                ANATOMICAL_SITES,
                help=(
                    "Central circulatory system and central nervous system "
                    "escalate classification to Class III."
                ),
            )
            connected_to_active_device = _yn(
                "Connected to an active device",
                help="Drives Rule 8 escalation.",
            )

            # ── 3. Duration of use ────────────────────────────────
            st.subheader("3. Duration of use")
            duration_of_use = st.selectbox(
                "Continuous use duration",
                DURATION,
                help=(
                    "Interrupted use of the same device counts cumulatively "
                    "toward the duration bucket."
                ),
            )

            # ── 4. Active device function ─────────────────────────
            st.subheader("4. Active device function")
            is_active_device = _yn("Active device")
            active_functions = []
            if is_active_device == "Yes":
                active_functions = st.multiselect(
                    "Active function(s)", ACTIVE_FUNCTIONS
                )
            hazardous_energy_administration = _yn(
                "Potentially hazardous energy administration",
                help="Escalates therapeutic actives to IIb.",
            )
            monitors_vital_immediate_danger = _yn(
                "Monitors vital parameters where variation could cause immediate danger",
                help="Escalates to IIb.",
            )
            integrated_closed_loop_diagnostic = _yn(
                "Integrated diagnostic function that significantly determines patient management",
                help="Rule 22, closed-loop, Class III.",
            )

            # ── 5. Software specifics (MDSW) ──────────────────────
            st.subheader("5. Software specifics (MDSW)")
            is_mdsw = _yn(
                "Standalone medical device software (MDSW)",
                help="Gates Rule 11 specifics.",
            )
            info_drives_decisions = "No"
            decision_significance = ""
            monitoring_role = ""
            drives_hardware_device = "No"
            if is_mdsw == "Yes":
                info_drives_decisions = _yn(
                    "Information drives diagnostic or therapeutic decisions"
                )
                decision_significance = st.selectbox(
                    "Decision significance", DECISION_SIGNIFICANCE
                )
                monitoring_role = st.selectbox("Monitoring role", MONITORING_ROLE)
                drives_hardware_device = _yn(
                    "Drives or controls a hardware device",
                    help=(
                        "If yes, the software inherits the host device's "
                        "classification pathway."
                    ),
                )

            # ── 6. Special-rule triggers ──────────────────────────
            st.subheader("6. Special-rule triggers")
            rule_14_medicinal_substance = st.checkbox(
                "Incorporates a medicinal substance with ancillary action "
                "(Rule 14, III)"
            )
            rule_18_non_viable_tissue = st.checkbox(
                "Incorporates non-viable human or animal tissue or derivative "
                "(Rule 18, III)"
            )
            rule_14_blood_derivative = st.checkbox(
                "Incorporates a human blood derivative (Rule 14, III)"
            )
            rule_15_contraception_or_sti = st.checkbox(
                "Intended for contraception or prevention of sexually "
                "transmitted infection (Rule 15)"
            )
            rule_16_disinfection = st.checkbox(
                "Specifically for disinfecting, cleaning or sterilising "
                "medical devices (Rule 16)"
            )
            rule_17_xray_images = st.checkbox(
                "Records diagnostic images generated by X-ray (Rule 17)"
            )
            rule_19_nanomaterial = st.checkbox(
                "Incorporates or consists of nanomaterial (Rule 19)"
            )
            nanomaterial_exposure_potential = ""
            if rule_19_nanomaterial:
                nanomaterial_exposure_potential = st.selectbox(
                    "Internal exposure potential", NANO_EXPOSURE
                )
            rule_20_inhalation = st.checkbox(
                "Administers medicines by inhalation via a body orifice (Rule 20)"
            )
            rule_21_absorbed_substance = st.checkbox(
                "Composed of substances absorbed by or locally dispersed in "
                "the body (Rule 21)"
            )

            # ── 7. Implementing meta ──────────────────────────────
            st.subheader("7. Implementing meta")
            user_type = st.selectbox("Intended user", USER_TYPES)
            use_environment = st.selectbox("Use environment", USE_ENVIRONMENTS)
            multiple_intended_uses = st.text_area(
                "Multiple intended uses",
                height=80,
                placeholder=(
                    "If the device has multiple intended uses, record the "
                    "most critical one — implementing rules classify on the "
                    "highest-risk intended use."
                ),
            )

            st.divider()
            submitted = st.form_submit_button(
                "Classify Device", type="primary", use_container_width=True
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
            # Section 6
            "rule_14_medicinal_substance": rule_14_medicinal_substance,
            "rule_18_non_viable_tissue": rule_18_non_viable_tissue,
            "rule_14_blood_derivative": rule_14_blood_derivative,
            "rule_15_contraception_or_sti": rule_15_contraception_or_sti,
            "rule_16_disinfection": rule_16_disinfection,
            "rule_17_xray_images": rule_17_xray_images,
            "rule_19_nanomaterial": rule_19_nanomaterial,
            "nanomaterial_exposure_potential": nanomaterial_exposure_potential,
            "rule_20_inhalation": rule_20_inhalation,
            "rule_21_absorbed_substance": rule_21_absorbed_substance,
            # Section 7
            "user_type": user_type,
            "use_environment": use_environment,
            "multiple_intended_uses": multiple_intended_uses.strip(),
        }
