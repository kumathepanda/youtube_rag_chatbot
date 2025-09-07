import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from config import VECTOR_STORE_ROOT_DIR, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, LLM_MODEL_NAME, MODEL_TEMPERATURE
from dotenv import load_dotenv
import time

load_dotenv()

# Initialize the LLM for translation
translation_llm = ChatGroq(model_name=LLM_MODEL_NAME, temperature=0.1)  # Lower temperature for translation accuracy
index_name = "talktube"
def detect_and_translate_transcript(transcript_text, source_language):
    """
    Translates non-English transcript to English using the LLM.
    """
    if source_language == 'en':
        return transcript_text
    
    print(f"Translating transcript from {source_language} to English...")
    
    # Split large text into smaller chunks for translation
    max_chunk_size = 3000  # Adjust based on your LLM's token limit
    chunks = []
    
    # Split text into manageable chunks
    words = transcript_text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1  # +1 for space
        if current_length > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    # Translation prompt template
    translation_prompt = ChatPromptTemplate.from_template("""
        You are a professional translator. Translate the following {source_lang} text to English accurately while preserving the meaning and context.
        
        Important guidelines:
        1. Maintain the original meaning and context
        2. Keep technical terms and proper nouns when appropriate
        3. Ensure the translation flows naturally in English
        4. Do not add any commentary or explanations, just provide the translation
        
        Text to translate:
        {text}
        
        English translation:
    """)
    
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        try:
            print(f"Translating chunk {i+1}/{len(chunks)}...")
            
            formatted_prompt = translation_prompt.format(
                source_lang=source_language,
                text=chunk
            )
            
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
        ytt_api = YouTubeTranscriptApi()
        
        # First, try to get English transcript directly
        try:
            fetched_transcript = ytt_api.fetch(video_id, languages=['en'])
            full_text = " ".join([snippet.text for snippet in fetched_transcript])
            print("Found English transcript")
            return full_text, 'en'
        except NoTranscriptFound:
            print("No English transcript found, looking for other languages...")
        
        # If no English transcript, list available transcripts and get the first one
        try:
            transcript_list = ytt_api.list(video_id)
            
            if not transcript_list:
                print("No transcripts available for this video")
                return None, None
            
            # Get the first available transcript
            first_transcript = list(transcript_list)[0]
            fetched_transcript = first_transcript.fetch()
            full_text = " ".join([snippet.text for snippet in fetched_transcript])
            language_code = first_transcript.language_code
            
            print(f"Found transcript in language: {language_code}")
            return full_text, language_code
            
        except Exception as e:
            print(f"Error getting transcript list: {e}")
            # Final fallback: try to get any transcript without specifying language
            try:
                fetched_transcript = ytt_api.fetch(video_id)
                full_text = " ".join([snippet.text for snippet in fetched_transcript])
                print("Found transcript (language unknown)")
                return full_text, 'unknown'
            except Exception as fallback_error:
                print(f"Final fallback also failed: {fallback_error}")
                return None, None
        
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
        return None, None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None, None

def process_video_transcript(video_id):
    """
    Enhanced function that processes video transcripts with translation support.
    """
    try:
        persist_directory = os.path.join(VECTOR_STORE_ROOT_DIR, video_id)
        
        # Check if already processed
        if os.path.exists(persist_directory):
            print(f"Video {video_id} already processed")
            return True
        
        # Get available transcript
        transcript_text, language_code = get_available_transcript(video_id)
        
        if transcript_text is None:
            print("No transcript available for processing")
            return False
        
        # Translate if not in English
        if language_code != 'en' and language_code != 'unknown':
            print(f"Translating from {language_code} to English...")
            try:
                transcript_text = detect_and_translate_transcript(transcript_text, language_code)
                print("Translation completed successfully")
            except Exception as e:
                print(f"Translation failed: {e}")
                print("Proceeding with original text...")
                # Continue with original text if translation fails
        elif language_code == 'unknown':
            print("Language unknown, attempting translation anyway...")
            try:
                transcript_text = detect_and_translate_transcript(transcript_text, 'unknown')
                print("Translation completed successfully")
            except Exception as e:
                print(f"Translation failed: {e}")
                print("Proceeding with original text...")
        
        # Process the (potentially translated) transcript
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.create_documents([transcript_text])
        
        # Create embeddings
        embeddings = HuggingFaceInferenceAPIEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # Store in vector database
        Pinecone.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=index_name,
            namespace=video_id
        )
        
        print(f"Successfully processed video {video_id} (original language: {language_code})")
        return True
        
    except Exception as e:
        print(f"Error processing video transcript: {e}")
        return False

def get_video_language_info(video_id):
    """
    Helper function to get language information about available transcripts.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        available_languages = []
        for transcript in transcript_list:
            available_languages.append({
                'language_code': transcript.language_code,
                'language': transcript.language,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            })
        
        return available_languages
        
    except Exception as e:
        print(f"Error getting language info: {e}")
        return []