FROM python:3.8.5
WORKDIR /home/bot
# Копирование оттуда, где Dockerfile туда, где workdir
COPY requirements.txt .
#  Исполняется из workdir
RUN pip install -r requirements.txt
COPY /bot .
COPY bot.py .