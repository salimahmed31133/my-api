from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
import yt_dlp
import os
import requests

app = Flask(__name__)
# CORS সেটিংস যাতে অন্য যেকোনো ওয়েবসাইট থেকে এপিআই কল করা যায়
CORS(app)

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    # ফ্রন্টএন্ড থেকে পাঠানো কোয়ালিটি বা এমপিথ্রি রিকোয়েস্ট রিসিভ করা
    requested_quality = request.args.get('quality')
    
    if not video_url:
        return jsonify({"success": False, "error": "URL missing"}), 400

    # কোয়ালিটি ও অডিও লজিক আপডেট (যাতে কাঙ্ক্ষিত কোয়ালিটি না থাকলেও প্রিভিউ আসে)
    if requested_quality == 'mp3':
        # শুধু অডিও বা গান নেওয়ার জন্য
        format_selection = 'bestaudio/best'
    elif requested_quality and requested_quality.isdigit():
        # লজিক: ইউজারের সিলেক্ট করা রেজোলিউশন অথবা তার নিচের সেরা রেজোলিউশন/অরিজিনাল ভিডিও নেবে
        format_selection = f'bestvideo[height<={requested_quality}]+bestaudio/best[height<={requested_quality}]/best'
    else:
        # ডিফল্ট সেরা ভিডিও
        format_selection = 'best'

    # yt-dlp কনফিগারেশন
    ydl_opts = {
        'format': format_selection,
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
            
            # সরাসরি ভিডিও/অডিও ইউআরএল সংগ্রহ
            download_link = info.get('url')
            
            # যদি প্লেলিস্ট বা স্লাইডশো হয় তবে প্রথমটি নেবে
            if not download_link and 'entries' in info:
                download_link = info['entries'][0].get('url')
            
            # --- ভিডিওর টাইটেল আপনার দেওয়া লজিক অনুযায়ী ফিক্সড রাখা হলো ---
            if requested_quality == 'mp3':
                title = "FreeSave_Download.mp3"
            else:
                title = "FreeSave_Download.mp4"
            # -------------------------------------------------------------

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
    # ফাইল নাম রিসিভ করা (save.html থেকে আসবে)
    filename = request.args.get('filename', 'FreeSave_Download.mp4')
    
    if not video_url:
        return "No URL provided", 400

    try:
        # ভিডিওর ডেটা স্ট্রিম হিসেবে নেওয়া
        req = requests.get(video_url, stream=True, timeout=30)
        
        # ভিডিওর মোট সাইজ বের করা
        total_size = req.headers.get('content-length')

        # লজিক: অডিও হলে audio/mpeg আর ভিডিও হলে video/mp4
        if filename.lower().endswith('.mp3'):
            mimetype = 'audio/mpeg'
        else:
            mimetype = 'video/mp4'

        def generate():
            for chunk in req.iter_content(chunk_size=8192):
                yield chunk

        # রেসপন্স তৈরি (mimetype সহ যাতে ব্রাউজার ও প্লেয়ার চিনতে পারে)
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
        }
        
        # যদি সাইজ পাওয়া যায়, তবে তা ব্রাউজারকে জানিয়ে দেওয়া
        if total_size:
            headers['Content-Length'] = total_size

        return Response(generate(), headers=headers, mimetype=mimetype)
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Render-এর পোর্টের সাথে অটোমেটিক কানেক্ট হওয়ার জন্য এই অংশটি মাস্ট
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
