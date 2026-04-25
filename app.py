from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from groq import Groq
import os, subprocess

app = Flask(__name__, static_folder='.')
CORS(app)

# ใส่ API Key ของน้องตรงนี้
client = Groq(api_key="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")

# กำหนดชื่อไฟล์ให้ชัดเจนเพื่อลดโอกาสเกิด FileNotFoundError
INPUT_VIDEO = "input_video.mp4"
OUTPUT_VIDEO = "output_video.mp4"
SRT_FILE = "sub.srt"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file"}), 400
            
        video = request.files['video']
        video.save(INPUT_VIDEO)
        
        with open(INPUT_VIDEO, "rb") as f:
            ts = client.audio.transcriptions.create(
                file=(INPUT_VIDEO, f.read()),
                model="whisper-large-v3",
                language="th",
                response_format="verbose_json"
            )
        
        # ส่งค่า Segment กลับไปให้ User แก้ไขบนหน้าเว็บ
        segments = [{"start": s['start'], "end": s['end'], "text": s['text']} for s in ts.segments]
        return jsonify({"segments": segments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/burn', methods=['POST'])
def burn():
    try:
        data = request.json
        subs = data.get('subs', [])
        
        # 1. สร้างไฟล์ SRT จากข้อมูลที่ผู้ใช้แก้คำผิดแล้ว
        srt_content = ""
        for i, s in enumerate(subs):
            srt_content += f"{i+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{s['text']}\n\n"
        
        with open(SRT_FILE, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # 2. ลบไฟล์เดิมก่อนเริ่มเรนเดอร์ (กันบัคไฟล์ซ้อนหรือหาไฟล์ไม่เจอ)
        if os.path.exists(OUTPUT_VIDEO):
            os.remove(OUTPUT_VIDEO)

        # 3. ใช้ FFmpeg ฝังซับ โดยระบุฟอนต์ที่ติดตั้งในเครื่อง
        # หมายเหตุ: ใน Linux Codespace ชื่อฟอนต์มักจะเป็น 'TH Sarabun New' หรือ 'Sarabun'
        cmd = [
            'ffmpeg', '-y', '-i', INPUT_VIDEO, 
            '-vf', f"subtitles={SRT_FILE}:force_style='FontName=TH Sarabun New,FontSize=28,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2'",
            '-c:a', 'copy', OUTPUT_VIDEO
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({"error": "FFmpeg Error", "details": result.stderr}), 500
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    if os.path.exists(OUTPUT_VIDEO):
        return send_file(OUTPUT_VIDEO, as_attachment=True)
    return "File not found", 404

def format_time(seconds):
    """แปลงวินาทีเป็นรูปแบบ SRT (00:00:00,000)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if __name__ == '__main__':
    # รันบน Port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
