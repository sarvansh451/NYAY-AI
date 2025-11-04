import streamlit as st
from dotenv import load_dotenv
from crew import legal_assistant_crew

load_dotenv()

st.set_page_config(page_title="NYAY AI Legal Assistant", page_icon="⚖️")

st.title("⚖️ NYAY AI - Your Legal Assistant")
st.markdown("""
Enter your legal issue below and get:
- Relevant IPC sections
- Legal analysis
- Suggested next steps
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Describe your legal issue..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your case..."):
            response = legal_assistant_crew.kickoff(inputs={"user_input": prompt})
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.markdown("---")
st.sidebar.markdown("**NYAY AI** - Legal Assistant")
st.sidebar.caption("Built with Streamlit")