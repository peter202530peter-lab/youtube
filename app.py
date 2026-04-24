from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze():
    video_url = request.json.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('height') and f.get('ext') == 'mp4':
                    formats.append({
                        'res': f"{f.get('height')}p",
                        'url': f.get('url')
                    })
            
            # فلترة باش نعطيو غير الجودات المزيانة بلا تكرار
            unique_formats = {f['res']: f for f in formats}.values()

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": list(unique_formats)[-3:] # أفضل 3 جودات
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # ضروري تكون 0.0.0.0 باش تخدم في منصات السحاب
    app.run(host='0.0.0.0', port=5000)