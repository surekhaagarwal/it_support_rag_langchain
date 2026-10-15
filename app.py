import streamlit as st
from dotenv import load_dotenv
from src.ingest import ROOT
from src.assistant import Assistant
load_dotenv(ROOT/'.env')
st.set_page_config(page_title='IT Support RAG',page_icon='🛠️')
st.title('IT Support Resolution Assistant')
st.caption('Prototype using synthetic incidents; no tickets are created.')
mode=st.selectbox('Retrieval method',['hybrid','semantic','bm25'])
question=st.text_area('Describe the IT issue',placeholder='My VPN disconnects when switching Wi-Fi networks')
@st.cache_resource

def get_assistant():
    return Assistant()


if st.button("Find guidance"):
    try:
        result, found = get_assistant().ask(question, mode)

        # print("DEBUG STATUS:", repr(result.status))
        # print("DEBUG SOURCES:", result.sources)

        # Display response status
        st.subheader(
            result.status.replace("_", " ").title()
        )

        # Display issue summary
        if result.issue_summary:
            st.write(result.issue_summary)

        # Clarification required
        if result.status == "NEEDS_CLARIFICATION":
            if result.clarifying_question:
                st.info(result.clarifying_question)

        # Human escalation required
        elif result.status.startswith("ESCALATE_"):
            st.warning(
                (result.escalation_reason or
                 "Insufficient evidence to provide guidance.")
                + " Human review is recommended; "
                  "no ticket has been created."
            )

        # Evidence-backed troubleshooting guidance
        elif result.status == "RESOLVED_GUIDANCE":
            for step in result.suggested_resolution:
                st.write("• " + step)

            if result.sources:
                st.write(
                    "Cited sources:",
                    ", ".join(result.sources)
                )

        # Keep retrieved records visible for debugging
        with st.expander("Debug: Retrieved documents (not necessarily cited)"):
            for r in found:
                st.markdown("**" + r["id"] + "**")

                scores = {
                    k: round(r[k], 4)
                    for k in (
                        "distance",
                        "similarity",
                        "bm25_score",
                        "rrf_score"
                    )
                    if k in r and r[k] is not None
                }

                st.write(scores)
                st.text(r["doc"].page_content)

    except Exception as exc:
        st.error(
            "Unable to process request. "
            "Check API key, index and dependencies. "
            + str(exc)
        )
