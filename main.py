from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import requests
from docx import Document
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Set up Gemini API
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)


# Function to extract video ID
def extract_video_id(youtube_url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(pattern, youtube_url)
    return match.group(1) if match else None


# API Route to Fetch Transcript with Better Error Handling
@app.route('/get_transcript', methods=['POST'])
def get_transcript():
    data = request.json
    video_url = data.get("url")
    video_id = extract_video_id(video_url)

    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Prioritized languages
        preferred_languages = ["en", "en-IN", "hi", "hi-IN"]
        selected_transcript = None

        # Try to fetch transcript in preferred order
        for lang in preferred_languages:
            try:
                selected_transcript = transcript_list.find_transcript([lang])
                break
            except:
                continue

        # If no preferred language is found, get any available transcript
        if not selected_transcript:
            selected_transcript = transcript_list.find_generated_transcript(
                [t.language_code for t in transcript_list]
            )

        # Extract transcript text
        text = " ".join([entry["text"] for entry in selected_transcript.fetch()])
        return jsonify({"transcript": text, "language": selected_transcript.language})

    except NoTranscriptFound:
        return jsonify({"error": "No transcript available for this video"}), 400
    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video"}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"YouTube request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Could not fetch transcript: {str(e)}"}), 500


# Serve the Webpage
@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
