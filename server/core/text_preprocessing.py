from youtube_transcript_api import YouTubeTranscriptApi,TranscriptsDisabled
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
load_dotenv()

video_id = "VxgH2HYasl4"
try:
    yt_api = YouTubeTranscriptApi()
    transcript_list = yt_api.list(video_id=video_id)
    transcript = transcript_list.find_generated_transcript(['en'])
    docs = transcript.fetch()
    full_text = " ".join([d.text for d in docs])
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
    chunks = splitter.create_documents([full_text])
    embeddings = HuggingFaceEndpointEmbeddings(repo_id="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma(persist_directory="storage/vectorstore",collection_name="Transcript_details",embedding_function=embeddings)
except TranscriptsDisabled:
    print("No captions available for this video")

