from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# ⚠️ ใช้ Key ของน้องครับ (พี่ใส่ไว้ให้แล้ว)
client = Groq(api_key="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")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'video' not in request.files:
        return jsonify({"error": "ไม่พบไฟล์วิดีโอ"}), 400
    
    video = request.files['video']
    file_path = "temp_upload.mp4"
    video.save(file_path)

    try:
        print("กำลังส่งเสียงไปประมวลผลบน Groq Cloud (ใช้ Whisper-Large-V3)...")
        # ส่งไปให้ Groq แปล (เพิ่ม Prompt จูนเสียงคนไทย/ฮิปฮอป)
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3", # แม่นยำที่สุด
                language="th",
                # 🔥 คำใบ้ดักคำเอ๋อ: เพิ่มคำศัพท์ที่น้องต้องการให้แม่นขึ้นตรงนี้
                prompt="สวัสดีครับ วันนี้เราอยู่กับยังโอม, YOUNGOHM, ธันวา, เพลงฮิปฮอป, ภาษาไทยวัยรุ่น, ธาตุทองซาวด์, โอเค, เข้าใจนะ, ครับ, ค่ะ, เชิญเลย, ดูนี่", 
                response_format="verbose_json"
            )
        
        # จัดรูปแบบข้อความให้แยกเป็นวินาทีสวยๆ
        formatted_text = ""
        for segment in transcription.segments:
            start = int(segment['start'])
            text = segment['text'].strip()
            if text:
                formatted_text += f"[{start}s] {text}\n"

        return jsonify({"subtitle": formatted_text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # ลบไฟล์ชั่วคราว
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
