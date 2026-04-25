from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# ใช้ Small เพื่อความเสถียรบน Codespaces
print("กำลังโหลด AI สมองระดับสูง (แบบเน้นความแม่นยำ)...")
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
        print("AI กำลังใช้สมาธิแกะเสียงภาษาไทย...")
        # ปรับจูนแบบละเอียดยิบ
        result = model.transcribe(
            file_path,
            language="th",
            # beam_size=10: ให้ AI คิดทบทวนคำสะกด 10 รอบก่อนพิมพ์ (ช้าแต่ชัวร์)
            beam_size=10,
            # best_of=5: สั่งให้สุ่มเดา 5 แบบแล้วเลือกอันที่ฟังดูเป็นมนุษย์ที่สุด
            best_of=5,
            # temperature=0: ห้ามเดามั่ว ให้เอาที่ใกล้เคียงความจริงที่สุด
            temperature=0,
            # condition_on_previous_text=False: ไม่เอาประโยคเก่ามาเดาประโยคใหม่ (กันการหลอน)
            condition_on_previous_text=False,
            initial_prompt="สวัสดีครับ ยินดีต้อนรับเข้าสู่ช่องของผม วันนี้เราจะมาทำอะไรสนุกๆ กันนะครับ",
            fp16=False
        )
        
        formatted_text = ""
        for segment in result['segments']:
            text = segment['text'].strip()
            # คัดกรองคำแปลกๆ ที่ AI ชอบหลอนออกมาเอง
            if text and len(text) > 1:
                start = int(segment['start'])
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
