import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from transcript_utils import extract_video_id, get_captions_yt_dlp, get_video_info, is_html_error
from pdf_utils import export_pdf

# Get Gemini API key from Streamlit secrets
gemini_api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=gemini_api_key)

st.title("YouTube Video Summarizer with PDF Notes Export")

url = st.text_input("Enter YouTube Video URL:")

# State for transcript and summary
if 'transcript_text' not in st.session_state:
    st.session_state['transcript_text'] = None
if 'summary' not in st.session_state:
    st.session_state['summary'] = None
if 'show_full_transcript' not in st.session_state:
    st.session_state['show_full_transcript'] = False

video_info = None

if url:
    video_id = extract_video_id(url)
    transcript_text = None
    if not video_id:
        st.error("Invalid YouTube URL.")
    else:
        with st.spinner("Fetching transcript..."):
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                transcript_text = " ".join([entry['text'] for entry in transcript])
            except Exception:
                try:
                    transcript_text = get_captions_yt_dlp(url)
                except Exception as e:
                    st.error(f"Could not fetch transcript or captions: {e}")
        if transcript_text and is_html_error(transcript_text):
            st.error("YouTube/Google has blocked the transcript request (CAPTCHA or automated query detected). Please try again later or with a different video.")
            transcript_text = None
        if transcript_text:
            st.session_state['transcript_text'] = transcript_text
            video_info = get_video_info(url)
        else:
            st.info("If you are repeatedly seeing this error, please wait a while or try a different network. YouTube may have temporarily blocked automated transcript requests from your IP.")

# Manual transcript upload always available if no transcript
if not st.session_state['transcript_text']:
    uploaded_file = st.file_uploader("Or upload a transcript text file (TXT)", type=["txt"])
    if uploaded_file is not None:
        st.session_state['transcript_text'] = uploaded_file.read().decode("utf-8")
        st.session_state['summary'] = None
        st.session_state['show_full_transcript'] = False

# If transcript is available, show preview, summary, and download
if st.session_state['transcript_text']:
    transcript_text = st.session_state['transcript_text']
    if not video_info and url:
        video_info = get_video_info(url)
    if video_info and video_info['thumbnail']:
        st.image(video_info['thumbnail'], use_column_width=True)
    st.subheader("Transcript Preview:")
    preview_len = 1000
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
    if st.session_state['summary']:
        st.subheader("Summary:")
        st.write(st.session_state['summary'])
        # Use video title for PDF filename
        video_title = video_info['title'] if video_info else 'summary'
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in video_title)
        pdf_filename = f"{safe_title}_notes.pdf"
        export_pdf(st.session_state['summary'], pdf_filename)
        with open(pdf_filename, "rb") as f:
            st.download_button("Download Notes as PDF", f, file_name=pdf_filename, mime="application/pdf") 