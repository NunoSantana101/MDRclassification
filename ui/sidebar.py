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

NANO_EXPOSURE = [
    "Negligible",
    "Low",
    "Medium or high",
]

R15_FORM = [
    "Barrier, oral or other non-invasive",
    "Implantable or long-term invasive",
]

R16_TARGET = [
    "Non-invasive medical devices",
    "Invasive medical devices",
    "Contact lenses",
]

R21_ACTION = [
    "Local action on skin or nasal/oral cavity (IIa)",
    "Local action elsewhere in the body (IIb)",
    "Systemically absorbed to achieve intended purpose (III)",
    "Acts in stomach or lower GI and is systemically absorbed (III)",
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
            st.caption("Tick only what applies. Sub-questions appear when needed.")

            rule_14_medicinal_substance = st.checkbox(
                "Incorporates a medicinal substance with ancillary action (Rule 14, III)"
            )
            rule_14_blood_derivative = st.checkbox(
                "Incorporates a human blood derivative (Rule 14, III)"
            )
            rule_18_non_viable_tissue = st.checkbox(
                "Incorporates non-viable human or animal tissue or derivative (Rule 18, III)"
            )

            rule_15_contraception_or_sti = st.checkbox(
                "Intended for contraception or prevention of sexually transmitted infection (Rule 15)"
            )
            _r15_pick = st.selectbox(
                "Form of the device",
                R15_FORM,
                index=0,
                help="Implantable or long-term invasive contraceptives → III; others → IIb.",
                disabled=not rule_15_contraception_or_sti,
                key="r15_form_pick",
            )
            rule_15_form = _r15_pick if rule_15_contraception_or_sti else ""

            rule_16_disinfection = st.checkbox(
                "Specifically disinfects, cleans, sterilises or hydrates medical devices (Rule 16)"
            )
            _r16_pick = st.selectbox(
                "What does it process?",
                R16_TARGET,
                index=0,
                help="Invasive devices or contact lenses → IIb; non-invasive → IIa.",
                disabled=not rule_16_disinfection,
                key="r16_target_pick",
            )
            rule_16_target = _r16_pick if rule_16_disinfection else ""

            rule_17_xray_images = st.checkbox(
                "Records diagnostic images generated by X-ray (Rule 17, IIb)"
            )

            rule_19_nanomaterial = st.checkbox(
                "Incorporates or consists of nanomaterial (Rule 19)"
            )
            _r19_pick = st.selectbox(
                "Internal exposure potential",
                NANO_EXPOSURE,
                index=0,
                help="Negligible → IIa, Low → IIb, Medium or high → III.",
                disabled=not rule_19_nanomaterial,
                key="r19_exposure_pick",
            )
            nanomaterial_exposure_potential = _r19_pick if rule_19_nanomaterial else ""

            rule_20_inhalation = st.checkbox(
                "Administers medicinal products by inhalation via a body orifice (Rule 20)"
            )
            _r20_pick = _toggle(
                "Mode of action has an essential impact on efficacy/safety, "
                "or is intended for life-threatening conditions",
                help='If "Yes" → Class IIb; otherwise → Class IIa.',
                disabled=not rule_20_inhalation,
            )
            rule_20_essential_to_efficacy = _r20_pick if rule_20_inhalation else "No"

            rule_21_absorbed_substance = st.checkbox(
                "Composed of substances introduced via body orifice or applied to the skin (Rule 21)"
            )
            _r21_pick = st.selectbox(
                "Mode of action",
                R21_ACTION,
                index=0,
                help="Selects the Rule 21 class.",
                disabled=not rule_21_absorbed_substance,
                key="r21_action_pick",
            )
            rule_21_action_mode = _r21_pick if rule_21_absorbed_substance else ""

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
            # Section 6
            "rule_14_medicinal_substance": rule_14_medicinal_substance,
            "rule_14_blood_derivative": rule_14_blood_derivative,
            "rule_18_non_viable_tissue": rule_18_non_viable_tissue,
            "rule_15_contraception_or_sti": rule_15_contraception_or_sti,
            "rule_15_form": rule_15_form,
            "rule_16_disinfection": rule_16_disinfection,
            "rule_16_target": rule_16_target,
            "rule_17_xray_images": rule_17_xray_images,
            "rule_19_nanomaterial": rule_19_nanomaterial,
            "nanomaterial_exposure_potential": nanomaterial_exposure_potential,
            "rule_20_inhalation": rule_20_inhalation,
            "rule_20_essential_to_efficacy": rule_20_essential_to_efficacy,
            "rule_21_absorbed_substance": rule_21_absorbed_substance,
            "rule_21_action_mode": rule_21_action_mode,
            # Section 7
            "user_type": user_type,
            "use_environment": use_environment,
            "multiple_intended_uses": multiple_intended_uses.strip(),
        }
