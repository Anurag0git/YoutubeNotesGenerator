from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import requests
import os
from dotenv import load_dotenv
from flask import send_from_directory
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
def get_content():
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

        # Extract transcript text properly
        # text = " ".join([entry.text for entry in selected_transcript.fetch()])
        text = " ".join([entry["text"] for entry in selected_transcript.fetch()])

        return jsonify({"transcript": text, "language": selected_transcript.language})

    except NoTranscriptFound:
        return jsonify({"error": "Not available for this video"}), 400
    except TranscriptsDisabled:
        return jsonify({"error": "Notes are disabled for this video"}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"YouTube request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Could not fetch content: {str(e)}"}), 500

# API Route to Generate Summary
@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    data = request.json
    transcript = data.get("transcript", "").strip()

    if not transcript:
        return jsonify({"error": "Content is empty"}), 400

    prompt = f"""
    Generate the most detailed, structured, and easy-to-remember notes from the given transcript. Follow these guidelines:

    1️⃣ **Simplify Complex Concepts**: Explain everything in the simplest way possible so that even a 10-year-old can understand.  
    2️⃣ **Use Step-by-Step Breakdown**: Organize content into structured sections with bullet points, key takeaways, and summaries.  
    3️⃣ **Add Analogies & Examples**: Relate concepts to real-life situations to make them more memorable.  
    4️⃣ **Highlight Key Points**: Emphasize important details with concise, impactful sentences.  
    5️⃣ **Make it Engaging**: Use a storytelling approach to maintain interest.  
    6️⃣ **Ensure Retention**: Format the information in a way that helps retain it long-term.  
    7️⃣ **Avoid Unnecessary Complexity**: No unnecessary details—just clear, practical, and useful knowledge.

    Only provide the notes without any introductions, headings, promotional text, or unnecessary comments.

    {transcript}
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        summary = response.text if response else "Failed to generate notes."
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": f"Could not generate notes: {str(e)}"}), 500

# Ensure the directory exists
os.makedirs("static/files", exist_ok=True)

@app.route('/save_summary', methods=['POST'])
def save_summary():
    data = request.json
    summary = data.get("summary", "").strip()

    if not summary:
        return jsonify({"error": "No notes to save!"}), 400

    file_path = "static/files/notes.pdf"

    # Create a PDF
    pdf = canvas.Canvas(file_path, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    # Add title
    pdf.drawString(100, 750, "Notes")

    # Add summary text (handling long text)
    y_position = 730
    for line in summary.split("\n"):
        pdf.drawString(100, y_position, line)
        y_position -= 20  # Move to next line

    pdf.save()

    return jsonify({"message": "Notes saved successfully!", "file": "notes.pdf"})

# Route to serve the file for download
@app.route('/download_summary')
def download_summary():
    return send_from_directory("static/files", "notes.pdf", as_attachment=True)


# Serve the Webpage
@app.route('/')
def home():
    return render_template('index.html')



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5555))
    app.run(host="0.0.0.0", port=port, debug=True)
