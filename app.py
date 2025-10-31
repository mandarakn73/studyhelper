import streamlit as st
import PyPDF2
import sqlite3
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

# -----------------------------
# SETUP
# -----------------------------
st.set_page_config(page_title="AI Study Assistant", layout="wide")

# Get your OpenAI key securely (you can also set it in Streamlit secrets)
openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    st.warning("⚠️ Please add your OpenAI API key in Streamlit secrets or environment variables.")
else:
    llm = ChatOpenAI(api_key=openai_api_key, model_name="gpt-4o-mini", temperature=0.4)

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("study_data.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                summary TEXT,
                flashcards TEXT,
                quiz TEXT
            )''')
conn.commit()

# -----------------------------
# FUNCTIONS
# -----------------------------
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def generate_summary(text):
    prompt = PromptTemplate.from_template("""
    Summarize the following lecture notes in simple, clear language suitable for students.
    Text: {text}
    """)
    response = llm.invoke(prompt.format(text=text))
    return response.content

def generate_flashcards(text):
    prompt = PromptTemplate.from_template("""
    From the following text, create 5 smart flashcards in this format:
    Q: <question>
    A: <answer>
    Text: {text}
    """)
    response = llm.invoke(prompt.format(text=text))
    return response.content

def generate_quiz(text):
    prompt = PromptTemplate.from_template("""
    Based on the text, create a short quiz with 5 multiple-choice questions.
    Format each as:
    Q: <question>
    A) option1
    B) option2
    C) option3
    D) option4
    Correct Answer: <letter>
    Text: {text}
    """)
    response = llm.invoke(prompt.format(text=text))
    return response.content

def save_to_db(filename, summary, flashcards, quiz):
    c.execute("INSERT INTO progress (filename, summary, flashcards, quiz) VALUES (?, ?, ?, ?)",
              (filename, summary, flashcards, quiz))
    conn.commit()

# -----------------------------
# STREAMLIT INTERFACE
# -----------------------------
st.title("📚 AI Study Assistant")
st.write("Upload your lecture notes and get summaries, flashcards, and quizzes!")

uploaded_file = st.file_uploader("Upload Lecture Notes (PDF)", type=["pdf"])

if uploaded_file is not None:
    filename = uploaded_file.name
    with st.spinner("Extracting text..."):
        text = extract_text_from_pdf(uploaded_file)

    st.subheader("📖 Extracted Text Preview")
    st.text_area("Preview", text[:1500] + "..." if len(text) > 1500 else text, height=200)

    if st.button("✨ Generate Study Materials"):
        with st.spinner("Generating summary..."):
            summary = generate_summary(text)

        with st.spinner("Creating flashcards..."):
            flashcards = generate_flashcards(text)

        with st.spinner("Preparing quiz..."):
            quiz = generate_quiz(text)

        st.success("✅ Study materials generated!")

        st.subheader("📝 Summary")
        st.write(summary)

        st.subheader("🎴 Flashcards")
        st.text(flashcards)

        st.subheader("🧩 Quiz")
        st.text(quiz)

        save_to_db(filename, summary, flashcards, quiz)
        st.info("✅ Progress saved to local database!")

# -----------------------------
# VIEW SAVED PROGRESS
# -----------------------------
st.sidebar.header("📂 Saved Studies")
if st.sidebar.button("Show Past Sessions"):
    rows = c.execute("SELECT filename, summary FROM progress").fetchall()
    for file, summary in rows:
        st.sidebar.write(f"**{file}**")
        st.sidebar.write(summary[:200] + "..." if len(summary) > 200 else summary)
