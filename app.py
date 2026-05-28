"""MDR Classification — Streamlit application.

Single-shot per query: each submission runs a fresh classification with
no carry-over from previous queries. At the end of every run, all stored
OpenAI Responses are deleted and an audit log is produced.
"""

from __future__ import annotations

import streamlit as st
from config import OPENAI_API_KEY
from ui.sidebar import render_sidebar
from ui.renderer import render_classification_result
from agents.orchestrator import run_classification_pipeline

st.set_page_config(
    page_title="MDR Classification",
    page_icon="*",
    layout="wide",
)

st.title("MDR Annex VIII Classification")
st.caption(
    "Structured deliberation support for MDR device classification. "
    "All outputs are provisional and require qualified human review."
)

if not OPENAI_API_KEY:
    st.error(
        "OpenAI API key not found. Create a `.env` file with "
        "`OPENAI_API_KEY=sk-...`, set the environment variable, "
        "or add it to Streamlit Cloud Secrets."
    )
    st.stop()

if "classification_result" not in st.session_state:
    st.session_state.classification_result = None
if "device_params" not in st.session_state:
    st.session_state.device_params = None

device_params = render_sidebar()

if device_params:
    st.session_state.classification_result = None
    st.session_state.device_params = device_params

    user_msg_lines = [
        "**Classify this device:**",
        "",
        f"- **Description:** {device_params['device_description']}",
        f"- **Intended purpose:** {device_params['intended_purpose']}",
        f"- **Invasiveness:** {device_params['invasiveness_category']}",
        f"- **Duration:** {device_params['duration_of_use']}",
        f"- **Active device:** {device_params['is_active_device']}",
        f"- **MDSW:** {device_params['is_mdsw']}",
        f"- **User:** {device_params['user_type']}",
        f"- **Environment:** {device_params['use_environment']}",
    ]
    user_msg = "\n".join(user_msg_lines)

    with st.chat_message("user"):
        st.markdown(user_msg)

    with st.chat_message("assistant"):
        status_container = st.status("Running MDR classification pipeline...", expanded=True)

        def on_status(msg: str):
            status_container.update(label=msg)
            status_container.write(msg)

        try:
            result = run_classification_pipeline(
                device_params,
                status_callback=on_status,
            )

            status_container.update(
                label="Classification complete", state="complete", expanded=False
            )

            st.session_state.classification_result = result

        except Exception as exc:
            status_container.update(label="Error", state="error", expanded=True)
            st.error(f"Pipeline error: {exc}")

if st.session_state.classification_result:
    render_classification_result(
        st.session_state.classification_result,
        st.session_state.device_params,
    )
