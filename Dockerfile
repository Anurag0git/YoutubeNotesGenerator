# Use an official Python runtime as a parent image
FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]
