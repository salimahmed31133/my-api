from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
# CORS সেটিংস যাতে অন্য যেকোনো ওয়েবসাইট থেকে তোর এপিআই কল করা যায়
CORS(app)

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"success": False, "error": "URL missing"}), 400

    # yt-dlp কনফিগারেশন: ফেসবুক, টিকটক ও সব প্ল্যাটফর্মের জন্য
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # সরাসরি ভিডিও ইউআরএল এবং টাইটেল সংগ্রহ
            download_link = info.get('url')
            
            # যদি প্লেলিস্ট বা স্লাইডশো হয় তবে প্রথমটি নেবে
            if not download_link and 'entries' in info:
                download_link = info['entries'][0].get('url')
            
            title = info.get('title', 'Video_Download')

        # রেসপন্স ডাটা
        result = {
            "success": True,
            "title": title,
            "url": download_link,
            "download_link": download_link
        }
        
        # স্পেশাল হেডার সেট করা যাতে ডাউনলোড বাটন কাজ করে
        response = make_response(jsonify(result))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/force_download')
def force_download():
    video_url = request.args.get('url')
    if not video_url:
        return "URL missing", 400
    
    try:
        # ভিডিও সোর্স থেকে ডাটা নিয়ে আসা
        r = requests.get(video_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        # এই হেডারগুলোই ব্রাউজারকে ডাউনলোড নোটিফিকেশন পাঠাতে বাধ্য করে
        headers = {
            'Content-Disposition': 'attachment; filename=FreeSave_Video.mp4',
            'Content-Type': 'video/mp4',
            'Access-Control-Allow-Origin': '*'
        }
        
        def generate():
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                yield chunk

        return Response(generate(), headers=headers)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Render-এর পোর্টের সাথে অটোমেটিক কানেক্ট হওয়ার জন্য এই অংশটি মাস্ট
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
