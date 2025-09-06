import os
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model_name="llama-3.1-8b-instant",temperature=0.4)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_rag_response(question, video_id):
    """
    Finds the answer to a question using the RAG pipeline for a specific video.
    """
    try:
        
        current_dir = os.path.dirname(os.path.realpath(__file__))
        server_dir = os.path.dirname(current_dir)
        persist_directory = os.path.join(server_dir, "storage", "vectorstore", video_id)

        if not os.path.exists(persist_directory):
            return "Error: Video has not been processed yet. Please process the video first."

        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

        prompt = ChatPromptTemplate.from_template("""
            Answer the following question based only on the provided context.
            Think step-by-step and provide a detailed answer.

            <context>
            {context}
            </context>

            Question: {input}
        """)
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        response = retrieval_chain.invoke({"input": question})
        
        return response["answer"]

    except Exception as e:
        print(f"An error occurred in the RAG pipeline: {e}")
        return "An error occurred while trying to answer the question."