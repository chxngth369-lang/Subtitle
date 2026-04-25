from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from groq import Groq
import os
import subprocess

app = Flask(__name__, static_folder='.')
CORS(app)

# ใส่ Key ของน้องครับ
client = Groq(api_key="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")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'video' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    video = request.files['video']
    file_path = "input_video.mp4"
    output_path = "output_video.mp4"
    video.save(file_path)

    try:
        # 1. แกะเสียงด้วย Groq (Whisper Large V3)
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                language="th",
                prompt="ยังโอม, YOUNGOHM, ภาษาไทยวัยรุ่น, เพลงฮิปฮอป",
                response_format="verbose_json"
            )
        
        # 2. สร้างไฟล์ซับไตเติ้ล (.srt)
        srt_content = ""
        for i, s in enumerate(transcription.segments):
            start = format_time(s['start'])
            end = format_time(s['end'])
            srt_content += f"{i+1}\n{start} --> {end}\n{s['text'].strip()}\n\n"
        
        with open("sub.srt", "w", encoding="utf-8") as f:
            f.write(srt_content)

        # 3. ฝังซับลงวิดีโอ (สีเหลือง ขอบดำ ตัวหนา)
        # ตัวกรอง subtitles จะอ่านไฟล์ sub.srt ไปแปะในวิดีโอ
        cmd = [
            'ffmpeg', '-y', '-i', file_path, 
            '-vf', "subtitles=sub.srt:force_style='FontSize=20,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2'",
            '-c:a', 'copy', output_path
        ]
        subprocess.run(cmd, check=True)

        return jsonify({
            "success": True,
            "segments": [{"start": s['start'], "end": s['end'], "text": s['text']} for s in transcription.segments]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    return send_file("output_video.mp4", as_attachment=True)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
