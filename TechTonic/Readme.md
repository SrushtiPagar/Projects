# 🚀 TechTonic — Think Smart. Code Smarter

**TechTonic** is an AI-powered chatbot built with Streamlit that helps users explore programming, Information Technology, and Computer Science concepts through an interactive conversational interface.

The chatbot uses a hosted AI model through the Groq API to generate responses, making it accessible through a web browser without requiring users to install a local AI model.

## ✨ Features

- 🤖 **AI-Powered Conversations** — Get explanations and answers to technical questions.
- 💻 **IT & Computer Science Focus** — Designed to answer questions related to programming, software development, and computer science.
- 💬 **Conversation History** — View previous messages during the current chat session.
- 🧹 **Clear Chat** — Reset the conversation and start a new discussion.
- 🌐 **Web-Based Interface** — Simple, interactive interface built with Streamlit.
- ⚡ **Hosted AI Integration** — Uses the Groq API to access a supported AI model.

## 🛠️ Tech Stack

- **Programming Language:** Python
- **Frontend / UI:** Streamlit
- **AI API:** Groq
- **AI Model:** `openai/gpt-oss-120b`
- **Deployment:** Streamlit Community Cloud
- **Version Control:** Git and GitHub

## 📂 Project Structure

```text
TechTonic/
│
├── TechTonic.py       # Main Streamlit application
├── requirements.txt   # Python dependencies
├── README.md          # Project documentation
└── .streamlit/
    └── secrets.toml   # Local API key configuration (keep private)
```

> **Note:** Never upload your actual API key or a `secrets.toml` file containing secrets to GitHub. Configure `GROQ_API_KEY` in Streamlit Community Cloud under your app's **Settings → Secrets**.

## ⚙️ How It Works

1. The user enters a question in the Streamlit chat interface.
2. The application stores the conversation in Streamlit session state.
3. The conversation is sent to the Groq API along with the system instructions.
4. The configured AI model generates a response.
5. TechTonic displays the answer and preserves the conversation history for the current session.

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/SrushtiPagar/Projects.git
```

### 2. Navigate to the project folder

```bash
cd Projects/TechTonic
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

Your `requirements.txt` should contain:

```text
streamlit
groq
```

### 5. Configure your API key

Create a `.streamlit` folder inside `TechTonic`, then create a `secrets.toml` file inside it:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Replace the placeholder with your own Groq API key. Keep this file private and do not commit it to GitHub.

### 6. Start the application

```bash
streamlit run TechTonic.py
```

Your browser should open the local application.

## ☁️ Deployment

TechTonic can be deployed using **Streamlit Community Cloud**.

1. Push your project files to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your GitHub account and select the repository.
4. Choose the `main` branch.
5. Set the main application file to `TechTonic/TechTonic.py` if deploying from the repository root.
6. Add your `GROQ_API_KEY` under the app's **Settings → Secrets**.
7. Deploy the application.

## 🔐 Security

- Store API keys in Streamlit Secrets or environment variables.
- Never hardcode private API keys in source code.
- Never commit secrets to a public repository.
- If an API key is accidentally exposed, revoke it and generate a replacement.

## 🎯 Future Enhancements

- 📚 Add curated programming learning resources.
- 🧠 Improve topic detection and technical-question handling.
- 📝 Add code examples and formatted code explanations.
- 🗂️ Support downloadable chat history.
- 🎨 Improve the user interface and customization options.

## 👩‍💻 Author

**Srushti Pagar**

GitHub: [@SrushtiPagar](https://github.com/SrushtiPagar)

---

*TechTonic — Think Smart. Code Smarter.*
