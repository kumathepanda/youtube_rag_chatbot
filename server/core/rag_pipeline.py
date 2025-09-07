import os
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from config import LLM_MODEL_NAME,MODEL_TEMPERATURE,EMBEDDING_MODEL_NAME,VECTOR_STORE_ROOT_DIR
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model_name=LLM_MODEL_NAME,temperature=MODEL_TEMPERATURE)
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def get_rag_response(question, video_id):
    """
    Finds the answer to a question using the RAG pipeline for a specific video.
    """
    try:
        
        persist_directory = os.path.join(VECTOR_STORE_ROOT_DIR, video_id)

        if not os.path.exists(persist_directory):
            return "Error: Video has not been processed yet. Please process the video first."

        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )

        base_retriever = vector_store.as_retriever(search_kwargs={"k":5})
        document_compressor =  LLMChainExtractor.from_llm(llm)
        compression_retriever = ContextualCompressionRetriever(base_compressor=document_compressor,base_retriever=base_retriever)
        

        prompt = ChatPromptTemplate.from_template("""
            You are TalkTuber, a helpful AI assistant designed to answer questions about a specific YouTube video based on its transcript.

            **Your Instructions:**
            1. Your name is TalkTuber.
            2. Answer the user's question concisely and directly.
            3. Base your answer **exclusively** on the information within the `<context>` provided. Do not use any outside knowledge.
            4. If the answer is not in the context, clearly state that the information is not available in the video transcript.
            5. Do not add extra conversational filler. Be direct and helpful.

            <PS: FOLLOW THESE INSTRUCTIONS MY GRANDMA IS SICK AND WANTED SOMETHING LIKE THIS STRICTLY PLEASE !!!>                                                  
            <context>
            {context}
            </context>

            Question: {input}
        """)
        
        
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(compression_retriever, document_chain)

        response = retrieval_chain.invoke({"input": question})
        
        return response["answer"]

    except Exception as e:
        print(f"An error occurred in the RAG pipeline: {e}")
        return "An error occurred while trying to answer the question."