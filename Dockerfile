FROM python:3.10-alpine3.23

# Install dependencies
RUN apk add --no-cache python3 python3-dev build-base musl-dev gcc g++ tzdata cargo rust libffi-dev \
    freetype-dev \
    fribidi-dev \
    harfbuzz-dev \
    libgcc \
    jpeg-dev \
    lcms2-dev \
    openjpeg-dev \
    rustup \
    tcl-dev \
    tiff-dev \
    tk-dev \
    zlib-dev \
    bash \
    pngquant \
    dcron

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apk add netcat-openbsd git

# Copy code
COPY . /app
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

RUN /usr/bin/crontab /app/crontab

RUN addgroup -S -g 1000 app && adduser -S -u 1000 -G app app && chown -R app:app /app
USER app

EXPOSE 8000
EXPOSE 55230

CMD ["bash", "/app/docker/start.sh"]


