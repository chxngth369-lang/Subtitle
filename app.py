from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from groq import Groq
import os, subprocess, time

app = Flask(__name__, static_folder='.')
CORS(app)

client = Groq(api_key="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")

# แก้บัค Path: ใช้ Absolute Path เพื่อให้หาไฟล์เจอแน่นอน
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
IN_VIDEO = os.path.join(CUR_DIR, "input_video.mp4")
OUT_VIDEO = os.path.join(CUR_DIR, "output_video.mp4")
SRT_FILE = os.path.join(CUR_DIR, "sub.srt")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        video = request.files['video']
        video.save(IN_VIDEO)
        with open(IN_VIDEO, "rb") as f:
            ts = client.audio.transcriptions.create(
                file=(IN_VIDEO, f.read()),
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
        
        # เขียนไฟล์ SRT ใหม่ทุกครั้ง
        content = ""
        for i, s in enumerate(subs):
            content += f"{i+1}\n{format_t(s['start'])} --> {format_t(s['end'])}\n{s['text']}\n\n"
        with open(SRT_FILE, "w", encoding="utf-8") as f:
            f.write(content)

        # ลบไฟล์เก่าทิ้งก่อนเรนเดอร์ใหม่
        if os.path.exists(OUT_VIDEO): os.remove(OUT_VIDEO)

        # สั่ง FFmpeg ฝังซับ (บังคับใช้ฟอนต์ Sarabun)
        cmd = [
            'ffmpeg', '-y', '-i', IN_VIDEO, 
            '-vf', f"subtitles={SRT_FILE}:force_style='FontName=TH Sarabun New,FontSize=28,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2'",
            '-c:a', 'copy', OUT_VIDEO
        ]
        subprocess.run(cmd, check=True)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    return send_file(OUT_VIDEO, as_attachment=True)

def format_t(sec):
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); ms = int((sec % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
