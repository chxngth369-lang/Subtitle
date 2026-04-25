from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from groq import Groq
import os, subprocess

app = Flask(__name__, static_folder='.')
CORS(app)

client = Groq(api_key="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")

# บังคับให้หาไฟล์ในโฟลเดอร์ปัจจุบันเท่านั้น
BASE_PATH = os.getcwd()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    video = request.files['video']
    video.save(os.path.join(BASE_PATH, "input_video.mp4"))
    with open("input_video.mp4", "rb") as f:
        ts = client.audio.transcriptions.create(
            file=("input_video.mp4", f.read()),
            model="whisper-large-v3",
            language="th",
            response_format="verbose_json"
        )
    return jsonify({"segments": [{"start": s['start'], "end": s['end'], "text": s['text']} for s in ts.segments]})

@app.route('/burn', methods=['POST'])
def burn():
    data = request.json
    subs = data.get('subs', [])
    srt_content = ""
    for i, s in enumerate(subs):
        srt_content += f"{i+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{s['text']}\n\n"
    
    with open(os.path.join(BASE_PATH, "sub.srt"), "w", encoding="utf-8") as f:
        f.write(srt_content)

    # สั่ง FFmpeg แบบเน้นๆ (เช็กฟอนต์ Sarabun)
    cmd = [
        'ffmpeg', '-y', '-i', 'input_video.mp4', 
        '-vf', "subtitles=sub.srt:force_style='FontName=TH Sarabun New,FontSize=28,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2'",
        '-c:a', 'copy', 'output_video.mp4'
    ]
    try:
        subprocess.run(cmd, check=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    path = os.path.join(BASE_PATH, "output_video.mp4")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "❌ ไฟล์ยังไม่ถูกสร้าง! กรุณากดปุ่ม 'ยืนยันและฝังซับ' ในหน้าเว็บก่อน", 404

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60); ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
