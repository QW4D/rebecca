FROM python:3.11.9-bookworm
WORKDIR /app
RUN apt-get -y update
RUN apt-get install -y ffmpeg
COPY ./requirements.txt .
RUN pip install -r ./requirements.txt
COPY . .
CMD ["python3","main.py"]
