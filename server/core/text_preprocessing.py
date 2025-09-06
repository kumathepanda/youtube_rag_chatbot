import os
from youtube_transcript_api import YouTubeTranscriptApi,TranscriptsDisabled
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
load_dotenv()

def get_transcript_of_video(video_id):
    try:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        server_dir = os.path.dirname(current_dir)
        persist_directory = os.path.join(server_dir, "storage", "vectorstore", video_id)
        yt_api = YouTubeTranscriptApi()
        transcript_list = yt_api.list(video_id=video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        docs = transcript.fetch()
        full_text = " ".join([d.text for d in docs])
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
        chunks = splitter.create_documents([full_text])
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = Chroma(persist_directory=persist_directory,collection_name="Transcript_details",embedding_function=embeddings)
        vector_store.add_documents(chunks)
        print("--------------------- RAN SUCCESSFULLY ----------------------------")
        return True
    except TranscriptsDisabled:
        print("No captions available for this video")
        return False

