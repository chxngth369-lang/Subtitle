from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# โหลด Model ขนาดเล็กเพื่อให้ประมวลผลได้เร็ว (เหมาะกับทรัพยากรจำกัด)
print("Loading AI Model... please wait.")
model = whisper.load_model("base")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'video' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    video = request.files['video']
    file_path = "temp_upload.mp4"
    video.save(file_path)

    try:
        # ใช้ AI ประมวลผลเสียงเป็นข้อความ (รองรับภาษาไทยอัตโนมัติ)
        result = model.transcribe(file_path)
        
        # ดึงเฉพาะข้อความมาแสดงผล
        formatted_text = ""
        for segment in result['segments']:
            start = int(segment['start'])
            text = segment['text']
            formatted_text += f"[{start}s] {text}\n"

        return jsonify({"subtitle": formatted_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    # รันบน port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
