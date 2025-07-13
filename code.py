import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from fpdf import FPDF
import re
import yt_dlp
import requests
import io

# Get Gemini API key from Streamlit secrets
gemini_api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=gemini_api_key)

st.title("YouTube Video Summarizer with PDF Notes Export")

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
            vtt = requests.get(url).text
            return vtt
    return None

# Helper to convert VTT to plain text
def vtt_to_text(vtt):
    lines = vtt.splitlines()
    text_lines = []
    for line in lines:
        if line.strip() == '' or re.match(r'\d{2}:\d{2}:\d{2}\.\d{3}', line) or re.match(r'\d+$', line):
            continue
        text_lines.append(line)
    return ' '.join(text_lines)

# PDF export helper
def export_pdf(summary, filename="summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
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
                    vtt = get_captions_yt_dlp(url)
                    if vtt:
                        transcript_text = vtt_to_text(vtt)
                except Exception as e:
                    st.error(f"Could not fetch transcript or captions: {e}")
        if transcript_text:
            st.subheader("Transcript Preview:")
            st.write(transcript_text[:1000] + ("..." if len(transcript_text) > 1000 else ""))
            if st.button("Summarize with Gemini"):
                with st.spinner("Summarizing..."):
                    model = genai.GenerativeModel('gemini-pro')
                    prompt = f"Summarize the following YouTube video transcript in concise notes:\n{transcript_text}"
                    try:
                        response = model.generate_content(prompt)
                        summary = response.text
                        st.subheader("Summary:")
                        st.write(summary)
                        # PDF export
                        pdf_filename = f"summary_{video_id}.pdf"
                        export_pdf(summary, pdf_filename)
                        with open(pdf_filename, "rb") as f:
                            st.download_button("Download Notes as PDF", f, file_name=pdf_filename, mime="application/pdf")
                    except Exception as e:
                        st.error(f"Gemini API error: {e}")
        else:
            st.error("Could not fetch transcript or captions for this video. The video may not have accessible subtitles or captions.")
