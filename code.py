import streamlit as st
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Access Gemini API key directly from Streamlit's secrets
gemini_api_key = st.secrets["GEMINI_API_KEY"]


# Prompt for generating detailed notes
prompt = """
Objective:
Generate detailed and structured notes using the transcript provided. The notes should be concise yet comprehensive, formatted for easy understanding, and presented in bullet points or organized sections. The target audience includes students, researchers, and knowledge enthusiasts looking for clear and actionable insights.

Guidelines for Note Creation:
1. **Topic Segmentation**:
   - Identify and separate key topics or themes within the transcript.
   - Use meaningful headings and subheadings for clarity.

2. **Key Points Extraction**:
   - Extract the most critical information from each section of the transcript.
   - Summarize concepts into clear, concise bullet points.

3. **Provide Context**:
   - Explain complex terms or ideas with simple examples or analogies.
   - Add background information if needed to enhance understanding.

4. **Visual Appeal**:
   - Use clear formatting with bullets, numbered lists, or tables where appropriate.
   - Keep the text organized and easy to skim.

5. **Actionable Insights**:
   - Include actionable takeaways or steps the reader can implement.
   - Highlight practical applications, if relevant.

6. **Interconnections**:
   - Establish links between different concepts to show their relevance or interdependence.
   - Provide examples or scenarios to illustrate these connections.

7. **Sources and References**:
   - If possible, recommend further reading or provide external references for deeper exploration.

Transcript:
{{Insert Transcript Here}}

Expected Output:
- Organized notes divided into headings and bullet points.
- Clear, concise explanations with emphasis on key points.
- Glossary or simple definitions for technical terms.
- Actionable insights or practical applications (if applicable).
"""

# Function to extract transcript details from YouTube video
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([i["text"] for i in transcript_text])
        return transcript
    except Exception as e:
        st.error(f"Error extracting transcript: {e}")
        return None

# Function to generate content using Gemini AI
def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        full_prompt = prompt + "\n\nTranscript:\n" + transcript_text
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

# Function to format the generated content into bullet points
def format_as_bullets(text):
    paragraphs = text.split('\n')
    formatted_text = ""
    for para in paragraphs:
        if para.strip():
            formatted_text += f"- {para.strip()}\n"
    return formatted_text

st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📚", layout="wide")

st.title("YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:")

# Extracting YouTube video ID from the provided link
def extract_youtube_link(youtube_link):
    match = re.search(r"youtube\.com\/watch\?v=([^\&]+)", youtube_link)
    if match:
        return "https://www.youtube.com/watch?v=" + match.group(1)
    else:
        st.error("Invalid YouTube link. Please enter a valid link.")
        return None

if youtube_link:
    youtube_link = extract_youtube_link(youtube_link)
    if youtube_link:
        video_id = youtube_link.split("=")[1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

if st.button("Get Detailed Notes"):
    if youtube_link:
        transcript_text = extract_transcript_details(youtube_link)
        if transcript_text:
            st.write("Extracted Transcript:")  # Debugging line to check transcript extraction
            st.write(transcript_text)  # Debugging line to check transcript extraction
            summary = generate_gemini_content(transcript_text, prompt)
            if summary:
                formatted_summary = format_as_bullets(summary)
                st.markdown("## Detailed Notes:")
                st.markdown(formatted_summary)