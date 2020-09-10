FROM python:3.8.5

RUN apt-get update && apt-get install --no-install-recommends --yes \
    libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio \
    gstreamer-1.0 \
    \
    python-gst-1.0 \
    libgirepository1.0-dev \
    libcairo2-dev \
    gir1.2-gtk-3.0 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade --no-cache-dir pip \
 && pip install --no-cache-dir poetry

WORKDIR /srv

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN poetry config virtualenvs.create false \
 && poetry install \
 && rm pyproject.toml poetry.lock
