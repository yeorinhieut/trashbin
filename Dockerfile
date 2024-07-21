FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r fastapi uvicorn aiohttp filetype pydantic

RUN pip install git+https://github.com/inside-dc/dcinside-python3-api.git

EXPOSE 8000

ENV GALLERY_ID=sff
ENV DELAY=10
ENV DEBUG=false

CMD ["python", "-u", "docker.py"]