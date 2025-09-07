import os

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

LLM_MODEL_NAME = "llama-3.1-8b-instant"

RETRIEVER_SEARCH_K = 5

MODEL_TEMPERATURE = 0.8

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 200

SERVER_DIR = os.path.dirname(os.path.realpath(__file__))

VECTOR_STORE_ROOT_DIR = os.path.join(SERVER_DIR, "storage", "vectorstore")
