from flask import Flask,jsonify,request
from core.text_preprocessing import get_transcript_of_video
from core.rag_pipeline import get_rag_response

app = Flask(__name__)

@app.route('/process-video',method=['POST'])
def process_video_route():
    data = request.get_json()
    video_id = data.get('videoId')

    if not video_id:
        return jsonify({"error":"Video Id is required"}) , 400
    success = get_transcript_of_video(video_id)

    if success:
        return jsonify({"message":f"video returned successfully {video_id}"})
    else:
        return jsonify({"error":"failed to process the video Id"}) , 500
    

@app.route('/chat',method=['POST'])
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
    
