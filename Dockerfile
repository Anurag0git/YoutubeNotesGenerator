# Use Python Alpine for a smaller image
FROM python:3.12.7-alpine

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install necessary system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev ffmpeg

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the Google API Key (Modify this at runtime)
ENV GOOGLE_API_KEY="AIzaSyBnTIV206lefAQ9UZ5h2svdDOwRjg0S14s"

# Expose port 5555 for external access
EXPOSE 5555

# Run Gunicorn server with Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5555", "main:app"]
