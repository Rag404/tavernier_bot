FROM docker.io/library/python:3.14.5-trixie AS build-stage

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/bot-env/bin:$PATH"


RUN python -m venv bot-env
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM docker.io/library/python:3.14.5-trixie AS runtime-stage

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/bot-env/bin:$PATH"


COPY --from=build-stage bot-env bot-env
COPY tavernier_main.py .

CMD ["python", "/app/tavernier_main.py"]
