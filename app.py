import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from transcript_utils import extract_video_id, get_captions_yt_dlp, get_video_info, is_html_error
from pdf_utils import export_pdf

st.set_page_config(page_title="YouTube Video Summarizer", page_icon=":movie_camera:", layout="wide")

st.markdown(
    """
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .stDownloadButton>button {background-color: #2196F3; color: white;}
    .stTextInput>div>div>input {background-color: #fff;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Get Gemini API key from Streamlit secrets
gemini_api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=gemini_api_key)

st.title("🎬 YouTube Video Summarizer with AI")
st.markdown("""Summarize any YouTube video and export concise notes as PDF. Paste a YouTube URL or upload a transcript file.""")

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
    # Layout: Thumbnail and Title
    if video_info and video_info['thumbnail']:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(video_info['thumbnail'], use_column_width=True)
        with col2:
            st.header(video_info['title'])
    st.markdown("---")
    st.markdown("#### Transcript Preview")
    preview_len = 1000
    if not st.session_state['show_full_transcript']:
        preview = transcript_text[:preview_len] + ("..." if len(transcript_text) > preview_len else "")
        st.write(preview)
        if len(transcript_text) > preview_len:
            if st.button("read more", key="read_more_btn"):
                st.session_state['show_full_transcript'] = True
    else:
        st.write(transcript_text)
    st.markdown("---")
    st.markdown("#### AI Summary & Export")
    col_sum, col_dl = st.columns([3, 1])
    with col_sum:
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
    with col_dl:
        if st.session_state['summary']:
            video_title = video_info['title'] if video_info else 'summary'
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in video_title)
            pdf_filename = f"{safe_title}_notes.pdf"
            export_pdf(st.session_state['summary'], pdf_filename)
            with open(pdf_filename, "rb") as f:
                st.download_button("Download Notes as PDF", f, file_name=pdf_filename, mime="application/pdf")
    st.markdown("---")

with st.expander("ℹ️ How does this work?"):
    st.write("""
    1. Paste a YouTube URL or upload a transcript file.
    2. The app fetches the transcript, summarizes it using Gemini AI, and lets you download notes as PDF.
    3. If you have issues, try uploading a transcript file manually.
    """)

st.markdown("---")
st.caption("Made with ❤️ using Streamlit and Gemini AI | [GitHub](https://github.com/) | [Contact](mailto:your@email.com)") 