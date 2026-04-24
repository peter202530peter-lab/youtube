from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)

# إعداد CORS للسماح لجميع النطاقات بالوصول (بما في ذلك GitHub Pages)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    # معالجة طلبات الاستكشاف (Preflight) التي يرسلها المتصفح تلقائياً
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({"error": "يرجى إدخال رابط فيديو صحيح"}), 400

        video_url = data.get('url')

        # إعدادات متقدمة لـ yt_dlp لضمان جلب روابط مباشرة صالحة
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            # إضافة User-Agent لتجنب الحظر من بعض المواقع
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats_list = []
            seen_res = set()
            
            # استخراج التنسيقات التي تحتوي على فيديو وصوت معاً بصيغة mp4
            all_formats = info.get('formats', [])
            for f in all_formats:
                height = f.get('height')
                # نفلتر الجودات الشائعة (360p, 720p, 1080p...)
                if height and f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    res = f"{height}p"
                    if res not in seen_res:
                        formats_list.append({
                            'res': res,
                            'url': f.get('url'),
                        })
                        seen_res.add(res)

            # فرز الجودات من الأقل إلى الأعلى
            formats_list.sort(key=lambda x: int(x['res'].replace('p', '')))

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats_list[-4:] # إعطاء أفضل 4 خيارات متاحة
            })
            
    except Exception as e:
        print(f"Error: {str(e)}") # سيظهر هذا في Logs المنصة
        return jsonify({"error": "فشل في تحليل الفيديو. تأكد من صحة الرابط."}), 500

if __name__ == '__main__':
    # جلب المنفذ من متغيرات البيئة (Railway تطلبه) أو استخدام 8080 كافتراضي بدلاً من 5000
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
