from flask import Flask,jsonify,request
from flask_cors import CORS
from core.text_preprocessing import process_video_transcript
from core.rag_pipeline import get_rag_response
from config import VECTOR_STORE_ROOT_DIR 
import os
app = Flask(__name__)

CORS(app)

@app.route('/video_status/<video_id>', methods=['GET'])
def video_status(video_id):
    """Checks if a vector store for the given video ID already exists."""
    persist_directory = os.path.join(VECTOR_STORE_ROOT_DIR, video_id)
    if os.path.exists(persist_directory):
        return jsonify({"status": "processed"})
    else:
        return jsonify({"status": "not_processed"})


@app.route('/process-video',methods=['POST'])
def process_video_route():
    data = request.get_json()
    video_id = data.get('videoId')

    if not video_id:
        return jsonify({"error":"Video Id is required"}) , 400
    success = process_video_transcript(video_id)

    if success:
        return jsonify({"message":f"video returned successfully {video_id}"})
    else:
        return jsonify({"error":"failed to process the video Id"}) , 500
    

@app.route('/chat',methods=['POST'])
def chat_route():
    data = request.get_json()
    video_id = data.get('videoId')
    question = data.get('question')

    if not video_id or not question:
        return jsonify({"error": "Video ID and question are required"}), 400

    answer = get_rag_response(question, video_id)
    
    return jsonify({"answer": answer})


if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)

