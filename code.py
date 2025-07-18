import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from fpdf import FPDF
import re
import yt_dlp
import requests
import io
import json

# Get Gemini API key from Streamlit secrets
gemini_api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=gemini_api_key)

st.title("YouTube Video Summarizer with AI")

# Helper to extract video ID from URL
def extract_video_id(url):
    match = re.search(r"(?:v=|youtu.be/)([\w-]{11})", url)
    return match.group(1) if match else None

# Helper to fetch captions using yt-dlp
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
                # Extract text from JSON captions
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

# Helper to detect HTML error responses

def is_html_error(text):
    return text.strip().lower().startswith("<html") or "<head>" in text.lower()

# Helper to convert VTT to plain text
def vtt_to_text(vtt):
    lines = vtt.splitlines()
    text_lines = []
    for line in lines:
        if line.strip() == '' or re.match(r'\d{2}:\d{2}:\d{2}\.\d{3}', line) or re.match(r'\d+$', line):
            continue
        text_lines.append(line)
    return ' '.join(text_lines)

# Helper to fetch video info (title and thumbnail) using yt-dlp

def get_video_info(video_url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            'title': info.get('title', 'summary'),
            'thumbnail': info.get('thumbnail', None)
        }

# PDF export helper
# Make sure DejaVuSans.ttf is in your project directory for Unicode support

def export_pdf(summary, filename="summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    # Add a Unicode font (DejaVuSans)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)
    for line in summary.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

url = st.text_input("Enter YouTube Video URL:")
if url:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("Invalid YouTube URL.")
    else:
        transcript_text = None
        with st.spinner("Fetching transcript..."):
            try:
                # Try youtube-transcript-api first
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                transcript_text = " ".join([entry['text'] for entry in transcript])
            except Exception:
                # Fallback to yt-dlp
                try:
                    transcript_text = get_captions_yt_dlp(url)
                except Exception as e:
                    st.error(f"Could not fetch transcript or captions: {e}")
        if transcript_text and is_html_error(transcript_text):
            st.error("YouTube/Google has blocked the transcript request (CAPTCHA or automated query detected). Please try again later or with a different video.")
            transcript_text = None
        if not transcript_text:
            st.info("If you are repeatedly seeing this error, please wait a while or try a different network. YouTube may have temporarily blocked automated transcript requests from your IP.")
        if transcript_text:
            video_info = get_video_info(url)
            if video_info['thumbnail']:
                st.image(video_info['thumbnail'], use_column_width=True)
            st.subheader("Transcript Preview:")
            preview_len = 1000
            if 'show_full_transcript' not in st.session_state:
                st.session_state['show_full_transcript'] = False
            if not st.session_state['show_full_transcript']:
                preview = transcript_text[:preview_len] + ("..." if len(transcript_text) > preview_len else "")
                st.write(preview)
                if len(transcript_text) > preview_len:
                    if st.button("read more", key="read_more_btn"):
                        st.session_state['show_full_transcript'] = True
            else:
                st.write(transcript_text)
            if st.button("Summarize with Gemini"):
                with st.spinner("Summarizing..."):
                    model = genai.GenerativeModel('gemini-2.5-pro')
                    prompt = f"Summarize the following YouTube video transcript in concise notes:\n{transcript_text}"
                    try:
                        response = model.generate_content(prompt)
                        summary = response.text
                        st.session_state['summary'] = summary
                    except Exception as e:
                        st.error(f"Gemini API error: {e}")
            # Always show summary and download if present in session_state
            if 'summary' in st.session_state:
                st.subheader("Summary:")
                st.write(st.session_state['summary'])
                # Use video title for PDF filename
                video_title = video_info['title']
                safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in video_title)
                pdf_filename = f"{safe_title}_notes.pdf"
                export_pdf(st.session_state['summary'], pdf_filename)
                with open(pdf_filename, "rb") as f:
                    st.download_button("Download Notes as PDF", f, file_name=pdf_filename, mime="application/pdf")
        # Show uploader at the bottom if transcript still not available
        if not transcript_text:
            uploaded_file = st.file_uploader("Or upload a transcript text file (TXT)", type=["txt"])
            if uploaded_file is not None:
                transcript_text = uploaded_file.read().decode("utf-8")
        else:
            st.error("Could not fetch transcript or captions for this video. The video may not have accessible subtitles or captions.")
