from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from reportlab.lib.utils import simpleSplit
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import requests
import os
from dotenv import load_dotenv
from flask import send_from_directory
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit


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
        # text = " ".join([entry.text for entry in selected_transcript.fetch()])   # use this when deploying
        text = " ".join([entry["text"] for entry in selected_transcript.fetch()]) # use this when testing on local machine

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
    language = data.get("language", "en").strip()  # default to English if not provided

    if not transcript:
        return jsonify({"error": "Content is empty"}), 400

    prompt = f"""
    Generate the most detailed, structured, and easy-to-remember notes TRANSLATE TO {language} LANGUAGE from the given transcript WITH APPROPRIATE CHARACTERS WHICH WOULD BE RECOGNISED IN .PDF FORMAT. Follow these guidelines:
    Only provide the notes WITHOUT any introductions, headings, promotional text, or unnecessary comments.
    AND DO NOT MENTION "TRANSCRIPT OR ANY RELATED WORD" ANYWHERE
    1️⃣ **Simplify Complex Concepts**: Explain everything in the simplest way possible so that even a 10-year-old can understand.  
    2️⃣ **Use Step-by-Step Breakdown**: Organize content into structured sections with bullet points, key takeaways, and summaries.  
    3️⃣ **Add Analogies & Examples**: Relate concepts to real-life situations to make them more memorable.  
    4️⃣ **Highlight Key Points**: Emphasize important details with concise, impactful sentences.  
    5️⃣ **Make it Engaging**: Use a storytelling approach to maintain interest.  
    6️⃣ **Ensure Retention**: Format the information in a way that helps retain it long-term.  
    7️⃣ **Avoid Unnecessary Complexity**: No unnecessary details—just clear, practical, and useful knowledge.


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

    # Add title with center alignment
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(300, 770, "Generated Notes")

    left_margin = 50
    right_margin = 550  # Ensuring text doesn't exceed the right margin
    y_position = 750
    max_width = right_margin - left_margin  # Limit text width
    max_lines_per_page = 35
    current_line = 0

    pdf.setFont("Helvetica", 12)
    for line in summary.split("\n"):
        wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)
        for sub_line in wrapped_lines:
            pdf.drawString(left_margin, y_position, sub_line[:100])  # Ensuring line doesn't exceed margins
            y_position -= 20
            current_line += 1

            # If the page is full, start a new page
            if current_line >= max_lines_per_page:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y_position = 750  # Reset position for the new page
                current_line = 0  # Reset line count

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
