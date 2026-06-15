FROM python:3.11-slim

# System dependencies (PortAudio) install karne ke liye
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

CMD ["uvicorn", "lotus:app", "--host", "0.0.0.0", "--port", "10000"]
