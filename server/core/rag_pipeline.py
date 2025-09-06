from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
load_dotenv()
model = ChatGroq(model_name="llama-3.1-8b-instant")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma(persist_directory="../storage/vectorstore",collection_name="Transcript_details",embedding_function=embeddings)
retriever = vector_store.as_retriever(search_type="similarity",search_kwargs={"k":3})
