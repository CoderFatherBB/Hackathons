import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from langchain_groq import ChatGroq
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ========= CONFIG =========
DATA_DIR = "data"
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# ========= HELPERS =========
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Splits text into chunks of a specified size with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

def extract_text_from_pdf(file_path):
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def transcribe_audio_groq(audio_path):
    """Transcribe audio using Whisper via Groq API"""
    with open(audio_path, "rb") as af:
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=af
        )
    return transcription.text

# ========= DATA INGESTION & CHUNKING =========
chunked_documents = []
for file in os.listdir(DATA_DIR):
    path = os.path.join(DATA_DIR, file)
    full_text = ""
    if file.endswith(".pdf"):
        print(f"Extracting and chunking PDF: {file}")
        full_text = extract_text_from_pdf(path)
    elif file.endswith(".txt"):
        print(f"Extracting and chunking TXT: {file}")
        full_text = extract_text_from_txt(path)
    elif file.endswith(".wav") or file.endswith(".mp3"):
        print(f"Transcribing and chunking Audio: {file}")
        full_text = transcribe_audio_groq(path)

    if full_text:
        chunks = chunk_text(full_text)
        for i, chunk in enumerate(chunks):
            chunked_documents.append((file, chunk))

# ========= EMBEDDINGS + FAISS INDEX =========
texts = [d[1] for d in chunked_documents]
embeddings = EMBED_MODEL.encode(texts, convert_to_numpy=True)

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print(f"Indexed {len(texts)} chunks from {len(set(d[0] for d in chunked_documents))} documents into FAISS vector DB.")

# ========= RAG RETRIEVAL + LLM =========
def retrieve_context(query, top_k=3):
    query_emb = EMBED_MODEL.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_emb, top_k)
    results = [chunked_documents[i][1] for i in indices[0]]
    sources = [chunked_documents[i][0] for i in indices[0]]
    return results, list(set(sources))

def ask_llm(query):
    context, sources = retrieve_context(query)
    context_text = "\n\n".join(context)

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0.2
    )

    prompt = f"""
    You are a helpful assistant. Use the context to answer the question.

    Context:
    {context_text}

    Question:
    {query}

    Answer with source references.
    """

    response = llm.invoke(prompt)
    print("\n--- ANSWER ---\n", response.content)
    print("\n--- SOURCES ---", sources)

# ========= TEST QUERY =========
if __name__ == "__main__":
    while True:
        q = input("Enter your question (or 'exit' to quit'): ")
        if q.lower() == 'exit':
            break
        ask_llm(q)
        print("\n")