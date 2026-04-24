from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)

# إعداد CORS بشكل يسمح للموقع في GitHub Pages بالاتصال بالسيرفر بدون قيود
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    # معالجة طلبات OPTIONS التي يرسلها المتصفح للتأكد من الأمان
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"error": "يرجى إدخال رابط صحيح"}), 400

    # إعدادات yt_dlp لجلب الروابط المباشرة بأفضل أداء
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # تجميع الجودات المتاحة بصيغة MP4
            formats_list = []
            seen_res = set()
            
            for f in info.get('formats', []):
                # نختار فقط الملفات التي تحتوي على فيديو وصوت معاً أو الفيديو بجودة واضحة
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    res = f"{f.get('height')}p"
                    if res not in seen_res and f.get('height'):
                        formats_list.append({
                            'res': res,
                            'url': f.get('url'),
                            'ext': f.get('ext')
                        })
                        seen_res.add(res)

            # إذا لم نجد جودات محددة، نأخذ الجودة الافتراضية
            if not formats_list:
                formats_list.append({
                    'res': 'Default Quality',
                    'url': info.get('url'),
                    'ext': info.get('ext')
                })

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats_list[-4:] # عرض آخر 4 جودات (الأعلى غالباً)
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Railway يستخدم متغير البيئة PORT لتحديد المنفذ تلقائياً
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
