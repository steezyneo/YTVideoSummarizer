import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from fpdf import FPDF
import re

# Get Gemini API key from Streamlit secrets
gemini_api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=gemini_api_key)

st.title("YouTube Video Summarizer with PDF Notes Export")

# Helper to extract video ID from URL
def extract_video_id(url):
    match = re.search(r"(?:v=|youtu.be/)([\w-]{11})", url)
    return match.group(1) if match else None

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
        with st.spinner("Fetching transcript..."):
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([entry['text'] for entry in transcript])
            except Exception as e:
                st.error(f"Could not fetch transcript: {e}")
                transcript_text = None
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
