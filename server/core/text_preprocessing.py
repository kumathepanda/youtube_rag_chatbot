import os
import time
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from config import EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, LLM_MODEL_NAME, MODEL_TEMPERATURE

load_dotenv()

# Initialize the LLM for translation
translation_llm = ChatGroq(model_name=LLM_MODEL_NAME, temperature=0.1)  # Lower temperature for translation accuracy
index_name = "talktube"  # Your Pinecone index name

def detect_and_translate_transcript(transcript_text, source_language):
    """
    Translates non-English transcript to English using the LLM.
    """
    if source_language == 'en':
        return transcript_text
    
    print(f"Translating transcript from {source_language} to English...")
    
    # Split large text into smaller chunks for translation
    max_chunk_size = 3000  # Adjust based on your LLM's token limit
    words = transcript_text.split()
    chunks = [" ".join(words[i:i + max_chunk_size]) for i in range(0, len(words), max_chunk_size)]
    
    # Translation prompt template
    translation_prompt = ChatPromptTemplate.from_template("""
        You are a professional translator. Translate the following {source_lang} text to English accurately while preserving the meaning and context.
        
        Important guidelines:
        1. Maintain the original meaning and context.
        2. Keep technical terms and proper nouns when appropriate.
        3. Ensure the translation flows naturally in English.
        4. Do not add any commentary or explanations, just provide the translation.
        
        Text to translate:
        {text}
        
        English translation:
    """)
    
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        try:
            print(f"Translating chunk {i+1}/{len(chunks)}...")
            
            formatted_prompt = translation_prompt.format(source_lang=source_language, text=chunk)
            
            response = translation_llm.invoke(formatted_prompt)
            translated_chunk = response.content.strip()
            translated_chunks.append(translated_chunk)
            
            # Add a small delay to avoid rate limiting
            if i < len(chunks) - 1:
                time.sleep(1)
                
        except Exception as e:
            print(f"Error translating chunk {i+1}: {e}")
            # Fallback: use original text if translation fails
            translated_chunks.append(chunk)
    
    return " ".join(translated_chunks)

def get_available_transcript(video_id):
    """
    Gets the best available transcript for a video, preferring English but accepting others.
    Returns transcript text and language code.
    """
    try:
        # First, try to get English transcript directly
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        full_text = " ".join([d['text'] for d in transcript])
        print("Found English transcript")
        return full_text, 'en'
    except (NoTranscriptFound, TranscriptsDisabled):
        print("No English transcript found, looking for other languages...")
        try:
            # If no English, list available and get the first one
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            first_transcript_info = next(iter(transcript_list))
            transcript = first_transcript_info.fetch()
            full_text = " ".join([d['text'] for d in transcript])
            language_code = first_transcript_info.language_code
            print(f"Found transcript in language: {language_code}")
            return full_text, language_code
        except Exception as e:
            print(f"Could not retrieve any transcript: {e}")
            return None, None

def process_video_transcript(video_id):
    """
    Processes video transcript and stores embeddings in Pinecone.
    """
    try:
        transcript_text, language_code = get_available_transcript(video_id)
        
        if transcript_text is None:
            print("No transcript available for processing")
            return False
        
        # Translate if not in English
        if language_code != 'en':
            print(f"Translating from {language_code} to English...")
            transcript_text = detect_and_translate_transcript(transcript_text, language_code)
            print("Translation completed successfully")
        
        # Process the (potentially translated) transcript
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.create_documents([transcript_text])
        
        # Create embeddings using the Hugging Face Inference API
        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            model_name=EMBEDDING_MODEL_NAME
        )
        
        # Store in Pinecone vector database, using video_id as the namespace
        Pinecone.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=index_name,
            namespace=video_id
        )
        
        print(f"Successfully processed and stored video {video_id} in Pinecone")
        return True
        
    except Exception as e:
        print(f"Error processing video transcript for Pinecone: {e}")
        return False

def get_video_language_info(video_id):
    """
    Helper function to get language information about available transcripts.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available_languages = [
            {
                'language_code': t.language_code,
                'language': t.language,
                'is_generated': t.is_generated,
            }
            for t in transcript_list
        ]
        return available_languages
    except Exception as e:
        print(f"Error getting language info: {e}")
        return []