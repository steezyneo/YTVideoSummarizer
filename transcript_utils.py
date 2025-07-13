import re
import yt_dlp
import requests
import json

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu.be/)([\w-]{11})", url)
    return match.group(1) if match else None

def get_captions_yt_dlp(video_url):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'subtitlesformat': 'vtt',
        'subtitleslangs': ['en'],
        'outtmpl': '%(id)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        subtitles = info.get('subtitles') or info.get('automatic_captions')
        if subtitles and 'en' in subtitles:
            url = subtitles['en'][0]['url']
            text = requests.get(url).text
            # Try to parse as JSON, else treat as VTT
            try:
                data = json.loads(text)
                events = data.get("events", [])
                transcript = []
                for event in events:
                    for seg in event.get("segs", []):
                        transcript.append(seg.get("utf8", ""))
                return " ".join(transcript)
            except Exception:
                # Not JSON, treat as VTT
                lines = text.splitlines()
                text_lines = []
                for line in lines:
                    if line.strip() == '' or re.match(r'\d{2}:\d{2}:\d{2}\.\d{3}', line) or re.match(r'\d+$', line):
                        continue
                    text_lines.append(line)
                return ' '.join(text_lines)
    return None

def get_video_info(video_url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            'title': info.get('title', 'summary'),
            'thumbnail': info.get('thumbnail', None)
        }

def is_html_error(text):
    return text.strip().lower().startswith("<html") or "<head>" in text.lower() 