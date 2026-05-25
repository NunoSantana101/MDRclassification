"""Sidebar form for device parameter input."""

from __future__ import annotations
import streamlit as st

DEVICE_TYPES = [
    "Standalone medical device software (MDSW)",
    "Active diagnostic device",
    "Implantable device",
    "Substance-based device",
    "Borderline / qualification boundary",
    "Other",
]

USER_TYPES = [
    "Lay user (general public)",
    "Lay user (patient with known condition)",
    "Healthcare professional (general practice)",
    "Healthcare professional (specialist)",
    "Healthcare professional (intensive care)",
    "Mixed lay and professional",
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


def render_sidebar() -> dict | None:
    """Render the sidebar form. Returns device params dict when submitted, else None."""
    with st.sidebar:
        st.header("Device Parameters")

        device_description = st.text_area(
            "Device description",
            height=120,
            placeholder="Describe the medical device in plain language...",
        )

        intended_purpose = st.text_area(
            "Intended purpose",
            height=80,
            placeholder="What is the device's intended medical purpose?",
        )

        device_type = st.selectbox("Device type", DEVICE_TYPES)
        user_type = st.selectbox("Intended user", USER_TYPES)
        use_environment = st.selectbox("Use environment", USE_ENVIRONMENTS)

        st.divider()
        submitted = st.button("Classify Device", type="primary", use_container_width=True)

        if submitted:
            if not device_description.strip():
                st.error("Please provide a device description.")
                return None
            if not intended_purpose.strip():
                st.error("Please provide the intended purpose.")
                return None

            return {
                "device_description": device_description.strip(),
                "intended_purpose": intended_purpose.strip(),
                "device_type": device_type,
                "user_type": user_type,
                "use_environment": use_environment,
            }

    return None
