FROM docker.io/library/python:3.14.5-trixie AS build-stage

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/bot-env/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv bot-env

RUN git clone https://github.com/An-Eagle/Tavernier-Bot /tmp/repo

RUN pip install --no-cache-dir -r /tmp/repo/requirements.txt

FROM docker.io/library/python:3.14.5-trixie AS runtime-stage

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/bot-env/bin:$PATH"

COPY --from=build-stage /bot-env /bot-env
COPY --from=build-stage /tmp/repo /

CMD ["python", "tavernier_main.py"]
