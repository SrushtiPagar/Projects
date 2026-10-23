import streamlit as st
from ollama import chat

st.set_page_config(page_title="TechTonic - IT & Computer Science AI", page_icon=":robot_face:")

st.title("TechTonic")
st.header("Think Smart. Code Smarter")

SYSTEM_PROMPT = """
You are a Python programming teacher specializing in IT and
Computer Science.

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
"""

# 1. Initialize chat history ONCE per session
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Display ALL previous questions and answers
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Input box for new questions
question = st.chat_input("Ask an IT or CS question...")

if question:
    # Add the new question to history
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Display the new question immediately
    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Include system prompt and entire conversation
                conversation = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }
                ] + st.session_state.messages

                response = chat(
                    model="llama3.2:1b",
                    messages=conversation
                )

                answer = response.message.content
                st.markdown(answer)

        # Save the answer so it remains visible
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as e:
        # Remove the unanswered question so it can be retried
        st.session_state.messages.pop()
        st.error(f"Unable to generate an answer: {e}")

# 4. Optional button to clear the conversation
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
