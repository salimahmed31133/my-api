from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
import yt_dlp
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    requested_quality = request.args.get('quality')
    
    if not video_url:
        return jsonify({"success": False, "error": "URL missing"}), 400

    # সাউন্ড নিশ্চিত করার জন্য লজিক আপডেট করা হয়েছে
    # এটি ভিডিও এবং অডিও আলাদাভাবে না খুঁজে, সরাসরি সাউন্ডসহ ফাইলটি খুঁজবে
    if requested_quality == 'mp3':
        format_selection = 'bestaudio/best'
    elif requested_quality and requested_quality.isdigit():
        # এই লজিকটি সেই ফাইলটি নেবে যেখানে অডিও ও ভিডিও একসাথে আছে (Single File)
        format_selection = f'best[height<={requested_quality}][ext=mp4]/best[height<={requested_quality}]/best'
    else:
        format_selection = 'best[ext=mp4]/best'

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
            
            # ডাউনলোড লিঙ্ক বের করার চেষ্টা
            download_link = info.get('url')
            
            # ব্যাকআপ লজিক (আপনার অরিজিনাল কোড অনুযায়ী)
            if not download_link:
                formats = info.get('formats', [])
                if formats:
                    download_link = formats[-1].get('url')

            if not download_link and 'entries' in info:
                download_link = info['entries'][0].get('url')
            
            if requested_quality == 'mp3':
                title = "FreeSave_Download.mp3"
            else:
                title = "FreeSave_Download.mp4"

        if not download_link:
            return jsonify({"success": False, "error": "Video link not found"}), 404

        result = {
            "success": True,
            "title": title,
            "url": download_link,
            "download_link": download_link
        }
        
        response = make_response(jsonify(result))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/force_download')
def force_download():
    video_url = request.args.get('url')
    filename = request.args.get('filename', 'FreeSave_Download.mp4')
    
    if not video_url:
        return "No URL provided", 400

    try:
        req = requests.get(video_url, stream=True, timeout=30)
        total_size = req.headers.get('content-length')

        if filename.lower().endswith('.mp3'):
            mimetype = 'audio/mpeg'
        else:
            mimetype = 'video/mp4'

        def generate():
            for chunk in req.iter_content(chunk_size=8192):
                yield chunk

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
        }
        if total_size:
            headers['Content-Length'] = total_size

        return Response(generate(), headers=headers, mimetype=mimetype)
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
