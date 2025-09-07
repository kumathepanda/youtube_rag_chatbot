from flask import Flask, jsonify, request
from flask_cors import CORS
from core.text_preprocessing import process_video_transcript, get_video_language_info
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

@app.route('/video_languages/<video_id>', methods=['GET'])
def video_languages(video_id):
    """Gets available language information for a video's transcripts."""
    try:
        language_info = get_video_language_info(video_id)
        if language_info:
            return jsonify({
                "available_languages": language_info,
                "has_english": any(lang['language_code'] == 'en' for lang in language_info),
                "needs_translation": not any(lang['language_code'] == 'en' for lang in language_info)
            })
        else:
            return jsonify({"error": "No transcripts available for this video"}), 404
    except Exception as e:
        return jsonify({"error": f"Error fetching language info: {str(e)}"}), 500

@app.route('/process-video', methods=['POST'])
def process_video_route():
    """Process video transcript with translation support."""
    data = request.get_json()
    video_id = data.get('videoId')

    if not video_id:
        return jsonify({"error": "Video ID is required"}), 400
    
    # Check if already processed
    persist_directory = os.path.join(VECTOR_STORE_ROOT_DIR, video_id)
    if os.path.exists(persist_directory):
        return jsonify({"message": f"Video {video_id} already processed", "status": "already_processed"})
    
    try:
        success = process_video_transcript(video_id)
        
        if success:
            return jsonify({
                "message": f"Video {video_id} processed successfully",
                "status": "processed"
            })
        else:
            return jsonify({
                "error": "Failed to process video. This could be due to: no transcripts available, transcripts disabled, or translation failed",
                "status": "failed"
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": f"An error occurred while processing: {str(e)}",
            "status": "error"
        }), 500

@app.route('/chat', methods=['POST'])
def chat_route():
    """Chat endpoint for asking questions about processed videos."""
    data = request.get_json()
    video_id = data.get('videoId')
    question = data.get('question')

    if not video_id or not question:
        return jsonify({"error": "Video ID and question are required"}), 400

    try:
        answer = get_rag_response(question, video_id)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "TalkTuber API is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)