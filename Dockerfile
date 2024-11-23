FROM cgr.dev/chainguard/wolfi-base

ARG version=3.12

WORKDIR /jerbot


RUN apk add python-${version} py${version}-pip && \
    chown -R nonroot:nonroot /jerbot/

COPY requirements.txt main.py err.py db.py scheduler.py .
COPY plugins plugins

# GCC is needed for the aarch64 images to compile Python packages.
RUN apk add gcc python-${version}-dev build-base && \
    pip install -r requirements.txt --user && \
    apk del gcc python-${version}-dev build-base

CMD ["python", "-O", "main.py"]
