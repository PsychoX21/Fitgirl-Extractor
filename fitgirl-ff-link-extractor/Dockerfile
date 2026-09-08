FROM python:3.11-slim-bookworm

# Prevent debconf interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies, Xvfb virtual frame buffer, and official Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    xvfb \
    x11-utils \
    libnss3 \
    libasound2 \
    libxss1 \
    libgbm1 \
    fonts-liberation \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Convert line endings (CRLF -> LF) and ensure executable permissions for Linux
RUN tr -d '\r' < start.sh > start_clean.sh && mv start_clean.sh start.sh && chmod +x start.sh

EXPOSE 8000

ENV PORT=8000
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

CMD ["./start.sh"]
