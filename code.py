import streamlit as st
from dotenv import load_dotenv
import re
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv("AIzaSyAoyNU7hAg74wuTWLckzjK4J0MERtCKndk"))

# Prompt for generating detailed notes
prompt = """
Prompt for Note-Making Bot using GEMINI AI TOOL
Objective:

The goal is to generate comprehensive notes using the Cornell Method infused with the principles of Anvinshiki. The notes should cover diverse topics relevant for knowledge acquisition, competitive exams preparation (specifically UPSC, JEE, and other technical examinations), and provide detailed explanations with relevant pictures and genuine sources for further reference.

Structure of the Notes:
1. Topic Identification:   

    Identify diverse topics within the domains of UPSC, JEE, and technical examinations.
    Prioritize topics based on importance, relevance, and frequency in exams.

2. Generate Overview:

    Provide a concise overview of each chosen topic, outlining key concepts and their applications.
    Include the significance of the topic in competitive exams.

3. Detailed Explanation:

    Utilize the Cornell Method to provide detailed explanations, breaking down complex concepts into simpler components.
    Ensure clarity in understanding and emphasize foundational principles.

4. Visual Aids:

    Incorporate relevant pictures, diagrams, and charts to enhance visual understanding.
    Ensure visual aids align with the explanations and serve as effective learning tools.

5. Anvinshiki Integration:

    Infuse principles of Anvinshiki, emphasizing holistic understanding and interconnectedness of topics.
    Establish relationships between different concepts to facilitate a deeper understanding.

6. Sources and References:

    Include genuine and reliable sources for each topic.
    Verify and provide clickable links for further studies, ensuring accessibility and authenticity.

7. Interactivity:

    Foster interactivity by incorporating quizzes, questions, and prompts for self-assessment.
    Encourage active engagement for better retention.

Explain each section in great detail and use simple terms and provide a glossary for difficult terms. Articulate the matter in a user-appeasing manner and in detail with simple understanding examples.
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
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

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