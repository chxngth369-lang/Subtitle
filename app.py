from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from groq import Groq
import os, subprocess, time

app = Flask(__name__, static_folder='.')
CORS(app)

client = Groq(api_key="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")

# แก้บัค Path: กำหนดตำแหน่งไฟล์ให้ชัดเจน
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_VIDEO = os.path.join(BASE_DIR, "input_video.mp4")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output_video.mp4")
SRT_FILE = os.path.join(BASE_DIR, "sub.srt")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        video = request.files['video']
        video.save(INPUT_VIDEO)
        with open(INPUT_VIDEO, "rb") as f:
            ts = client.audio.transcriptions.create(
                file=(INPUT_VIDEO, f.read()),
                model="whisper-large-v3",
                language="th",
                response_format="verbose_json"
            )
        return jsonify({"segments": [{"start": s['start'], "end": s['end'], "text": s['text']} for s in ts.segments]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/burn', methods=['POST'])
def burn():
    try:
        data = request.json
        subs = data.get('subs', [])
        
        # สร้าง SRT
        srt_content = ""
        for i, s in enumerate(subs):
            srt_content += f"{i+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{s['text']}\n\n"
        
        with open(SRT_FILE, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # แก้บัค Font: ใช้ TH Sarabun New และลบไฟล์เก่าก่อนเริ่ม
        if os.path.exists(OUTPUT_VIDEO): os.remove(OUTPUT_VIDEO)
        
        cmd = [
            'ffmpeg', '-y', '-i', INPUT_VIDEO, 
            '-vf', f"subtitles={SRT_FILE}:force_style='FontName=TH Sarabun New,FontSize=26,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2'",
            '-c:a', 'copy', OUTPUT_VIDEO
        ]
        subprocess.run(cmd, check=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    # แก้บัคดาวน์โหลด: เช็กว่าไฟล์มีจริงไหมก่อนส่ง
    if os.path.exists(OUTPUT_VIDEO):
        return send_file(OUTPUT_VIDEO, as_attachment=True)
    return "ไฟล์ยังไม่พร้อม", 404

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60); ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
