"""MDR Classification — Streamlit application.

Chat-style interface with sidebar form for device parameters.
Orchestrates nano agents via gpt-5.4-mini composition agent.
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

if "messages" not in st.session_state:
    st.session_state.messages = []
if "classification_result" not in st.session_state:
    st.session_state.classification_result = None

device_params = render_sidebar()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.classification_result:
    render_classification_result(st.session_state.classification_result)

if device_params:
    user_msg = (
        f"**Classify this device:**\n\n"
        f"- **Description:** {device_params['device_description']}\n"
        f"- **Intended purpose:** {device_params['intended_purpose']}\n"
        f"- **Type:** {device_params['device_type']}\n"
        f"- **User:** {device_params['user_type']}\n"
        f"- **Environment:** {device_params['use_environment']}"
    )
    st.session_state.messages.append({"role": "user", "content": user_msg})

    with st.chat_message("user"):
        st.markdown(user_msg)

    with st.chat_message("assistant"):
        status_container = st.status("Running MDR classification pipeline...", expanded=True)

        def on_status(msg: str):
            status_container.update(label=msg)
            status_container.write(msg)

        try:
            result = run_classification_pipeline(
                device_description=device_params["device_description"],
                intended_purpose=device_params["intended_purpose"],
                device_type=device_params["device_type"],
                user_type=device_params["user_type"],
                use_environment=device_params["use_environment"],
                status_callback=on_status,
            )

            status_container.update(
                label="Classification complete", state="complete", expanded=False
            )

            st.session_state.classification_result = result
            render_classification_result(result)

            v4 = result.get("v4_output", {})
            s1 = v4.get("section_1_final_mdr_device_classification", {})
            summary = s1.get("single_sentence_statement", "Classification complete.")
            st.session_state.messages.append({"role": "assistant", "content": summary})

        except Exception as exc:
            status_container.update(label="Error", state="error", expanded=True)
            st.error(f"Pipeline error: {exc}")
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Error: {exc}"}
            )
