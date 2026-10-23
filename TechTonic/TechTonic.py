
import streamlit as st
from groq import Groq

st.set_page_config(page_title="TechTonic", page_icon="💻")

st.title("TechTonic")
st.header("Think Smart. Code Smarter")

SYSTEM_PROMPT = """
You are TechTonic, a Python programming teacher
specializing in IT and Computer Science.

Answer only questions related to:
- Programming languages
- Data Structures and Algorithms
- Operating Systems
- DBMS and Computer Networks
- Software Engineering
- Web Development
- AI, Machine Learning and Data Science
- Cybersecurity, Cloud Computing and Git

If a question is unrelated to IT or Computer Science,
politely refuse to answer it.
Explain concepts clearly using examples when useful.
"""

# Initialize chat history once per session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask an IT or CS question...")

if question:
    # Save and display the user's question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    try:
        # Read the API key from Streamlit Secrets
        client = Groq(
            api_key=st.secrets["GROQ_API_KEY"]
        )

        # Send the full conversation to the hosted model
        conversation = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + st.session_state.messages

        with st.chat_message("assistant"):
            with st.spinner("TechTonic is thinking..."):
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=conversation,
                    temperature=0.5,
                    max_tokens=1024
                )

                answer = response.choices[0].message.content
                st.markdown(answer)

        # Save the answer for future turns
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as e:
        # Remove the unanswered question so it can be retried
        st.session_state.messages.pop()
        st.error(
            "Unable to generate an answer. "
            "Please check your API key, model access, "
            "and deployment logs."
        )
        st.caption(f"Error details: {e}")

# Clear conversation
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
