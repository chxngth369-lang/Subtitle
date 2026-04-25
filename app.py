from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# ใช้รุ่น Small เพราะบาลานซ์ระหว่างความเร็วและความฉลาดได้ดีที่สุดบนเครื่องฟรี
print("กำลังโหลด AI สมองระดับสูง (CapCut Style)...")
model = whisper.load_model("small")

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
        print("AI กำลังวิเคราะห์เสียงพูดแบบละเอียด...")
        # ปรับจูนให้ฉลาดแบบ CapCut
        result = model.transcribe(
            file_path,
            language="th",
            # initial_prompt: ช่วยให้ AI เข้าใจบริบทภาษาไทย และคำศัพท์วัยรุ่น/ชื่อเฉพาะ
            initial_prompt="สวัสดีครับ ผมชื่อเนท วันนี้เราจะมาทำคลิปสนุกๆ กันนะครับ", 
            # beam_size: ให้ AI คิดหลายรอบก่อนเลือกคำที่ถูกต้องที่สุด (ยิ่งเยอะยิ่งแม่น แต่จะช้าลง)
            beam_size=5,
            # temperature: ปรับให้ AI ไม่เดามั่วจนเกินไป
            temperature=0,
            fp16=False
        )
        
        formatted_text = ""
        for segment in result['segments']:
            start = int(segment['start'])
            # ตัดช่องว่างส่วนเกินออกเพื่อให้ดูสะอาดแบบ Subtitle จริงๆ
            text = segment['text'].strip()
            if text:
                formatted_text += f"[{start}s] {text}\n"

        return jsonify({"subtitle": formatted_text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
