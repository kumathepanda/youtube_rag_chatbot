import os
from youtube_transcript_api import YouTubeTranscriptApi,TranscriptsDisabled
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import VECTOR_STORE_ROOT_DIR,EMBEDDING_MODEL_NAME,CHUNK_SIZE,CHUNK_OVERLAP
from dotenv import load_dotenv
load_dotenv()

def get_transcript_of_video(video_id):
    try:
        persist_directory = os.path.join(VECTOR_STORE_ROOT_DIR, video_id)
        yt_api = YouTubeTranscriptApi()
        transcript_list = yt_api.list(video_id=video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        docs = transcript.fetch()
        full_text = " ".join([d.text for d in docs])
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE,chunk_overlap=CHUNK_OVERLAP)
        chunks = splitter.create_documents([full_text])
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        print("--------------------- RAN SUCCESSFULLY ----------------------------")
        return True
    except TranscriptsDisabled:
        print("No captions available for this video")
        return False

