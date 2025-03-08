import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from docx import Document
from PIL import Image, ImageTk

# Set up Gemini API
GEMINI_API_KEY = "AIzaSyBnTIV206lefAQ9UZ5h2svdDOwRjg0S14s"
genai.configure(api_key=GEMINI_API_KEY)


# Function to extract video ID
def extract_video_id(youtube_url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(pattern, youtube_url)
    return match.group(1) if match else None


# Function to fetch transcript
def get_transcript():
    video_url = url_entry.get()
    video_id = extract_video_id(video_url)

    if not video_id:
        messagebox.showerror("Error", "Invalid YouTube URL")
        return

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi', 'hi-IN'])
        text = " ".join([entry["text"] for entry in transcript])
        transcript_text.delete("1.0", tk.END)
        transcript_text.insert(tk.END, text)
    except Exception as e:
        messagebox.showerror("Error", f"Could not fetch transcript: {e}")


# Function to generate summary
def generate_summary():
    transcript = transcript_text.get("1.0", tk.END).strip()
    if not transcript:
        messagebox.showerror("Error", "Please fetch the transcript first!")
        return

    prompt = f"Generate detailed notes for each section in the given transcript in simple English:\n\n{transcript}"

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        summary = response.text if response else "Failed to generate summary."

        summary_text.delete("1.0", tk.END)
        summary_text.insert(tk.END, summary)
    except Exception as e:
        messagebox.showerror("Error", f"Could not generate summary: {e}")


# Function to save summary as .docx
def save_summary():
    summary = summary_text.get("1.0", tk.END).strip()
    if not summary:
        messagebox.showerror("Error", "No summary to save!")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Document", "*.docx")])
    if file_path:
        doc = Document()
        doc.add_heading("YouTube Video Summary", level=1)
        doc.add_paragraph(summary)
        doc.save(file_path)
        messagebox.showinfo("Success", "Summary saved successfully!")


# UI Setup
root = tk.Tk()
root.title("YouTube Summarizer")
root.geometry("600x650")
root.configure(bg="#f9f9f9")

# Load and display an image
image = Image.open("youtube_icon.png")  # Add your own logo image
image = image.resize((80, 80))
photo = ImageTk.PhotoImage(image)
logo_label = tk.Label(root, image=photo, bg="#f9f9f9")
logo_label.pack(pady=10)

# URL Entry
tk.Label(root, text="Enter YouTube URL:", font=("Arial", 12), bg="#f9f9f9").pack()
url_entry = tk.Entry(root, width=50, font=("Arial", 12))
url_entry.pack(pady=5)

# Buttons
fetch_btn = tk.Button(root, text="Fetch Transcript", font=("Arial", 12), bg="#ff5757", fg="white",
                      command=get_transcript)
fetch_btn.pack(pady=5)

summary_btn = tk.Button(root, text="Generate Summary", font=("Arial", 12), bg="#4287f5", fg="white",
                        command=generate_summary)
summary_btn.pack(pady=5)

# Transcript Textbox
tk.Label(root, text="Transcript:", font=("Arial", 12), bg="#f9f9f9").pack()
transcript_text = tk.Text(root, height=8, width=70, wrap="word", font=("Arial", 10))
transcript_text.pack(pady=5)

# Summary Textbox
tk.Label(root, text="Generated Summary:", font=("Arial", 12), bg="#f9f9f9").pack()
summary_text = tk.Text(root, height=8, width=70, wrap="word", font=("Arial", 10))
summary_text.pack(pady=5)

# Save Button
save_btn = tk.Button(root, text="Save as .docx", font=("Arial", 12), bg="#32a852", fg="white", command=save_summary)
save_btn.pack(pady=10)

# Run App
root.mainloop()
