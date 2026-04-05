FROM python:3.14-slim-trixie

ENV DASH_DEBUG_MODE False

RUN apt update && \
    apt install -y \
        make \
        build-essential \
        zlib1g-dev \
        libbz2-dev \
        liblzma-dev

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 8050
# gunicorn -b 0.0.0.0:8050 'cencyclopedia.app:server()'
CMD ["gunicorn", "-b", "0.0.0.0:8050", "'cencyclopedia.app:server()'"]
