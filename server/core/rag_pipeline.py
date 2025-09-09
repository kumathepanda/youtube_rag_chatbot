import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_pinecone import Pinecone
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from config import LLM_MODEL_NAME, MODEL_TEMPERATURE, EMBEDDING_MODEL_NAME

load_dotenv()

index_name = "talktube"  # Your Pinecone index name

def get_rag_response(question, video_id, api_key):
    """
    Finds the answer to a question using the RAG pipeline with Pinecone.
    This function now uses a user-provided API key for the LLM.
    """
    try:
        # Initialize LLM inside the function with the user-provided API key
        llm = ChatGroq(
            model_name=LLM_MODEL_NAME, 
            temperature=MODEL_TEMPERATURE,
            groq_api_key=api_key  # Use the key passed from the request
        )

        # Initialize embeddings using the Hugging Face Inference API
        # (This uses a separate, developer-provided API key from .env)
        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            model_name=EMBEDDING_MODEL_NAME
        )
        
        # Load the vector store from an existing Pinecone index
        vector_store = Pinecone.from_existing_index(
            index_name=index_name,
            embedding=embeddings,
            namespace=video_id  # Use the video_id to isolate documents
        )

        # Create a retriever from the vector store
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        
        # Optional: Use a compressor for more relevant results, using the user-specific LLM
        document_compressor = LLMChainExtractor.from_llm(llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=document_compressor,
            base_retriever=base_retriever
        )
        
        # Define the prompt template
        prompt = ChatPromptTemplate.from_template("""
            You are TalkTuber, a helpful AI assistant designed to answer questions about a specific YouTube video based on its transcript.

            **Your Instructions:**
            1. Your name is TalkTuber.
            2. Answer the user's question concisely and directly.
            3. Base your answer **exclusively** on the information within the `<context>` provided. Do not use any outside knowledge.
            4. If the answer is not in the context, clearly state that the information is not available in the video transcript.
            5. Do not add extra conversational filler. Be direct and helpful.
                                                  
            <context>
            {context}
            </context>

            Question: {input}
        """)
        
        # Create the RAG chain using the user-specific LLM
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(compression_retriever, document_chain)

        # Invoke the chain to get a response
        response = retrieval_chain.invoke({"input": question})
        
        return response["answer"]

    except Exception as e:
        # Handle specific API key errors from Groq
        if "invalid api key" in str(e).lower():
            return "Error: The provided Groq API key is invalid. Please check your key in the extension settings."
        # Check for a specific error when a namespace (video_id) doesn't exist yet
        if "provided namespace" in str(e) and "does not exist" in str(e):
             return "Error: This video has not been processed yet. Please click 'Process Video' first."
        print(f"An error occurred in the RAG pipeline with Pinecone: {e}")
        return "An error occurred while trying to answer the question. Please ensure the video is processed."