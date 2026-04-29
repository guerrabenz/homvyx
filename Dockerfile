# Use Python 3.10 slim as base
FROM python:3.10-slim

# Install FFmpeg and fonts (required for video processing and drawtext)
RUN apt-get update && \
    apt-get install -y ffmpeg fonts-liberation cron tzdata && \
    rm -rf /var/lib/apt/lists/*

# Set timezone to EST (or any preferred timezone for the 9AM trigger)
ENV TZ="America/New_York"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Ensure the output directories exist
RUN mkdir -p output/videos output/images output/audio output/scripts

# Make the start script executable
RUN chmod +x start.sh

# The container will run the start.sh script which sets up the cron job and keeps it alive
CMD ["./start.sh"]
