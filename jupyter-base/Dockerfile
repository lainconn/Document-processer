FROM ubuntu:latest

WORKDIR /app
RUN mkdir /data

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && apt-get --no-install-recommends install -y \
        python3-pip \
        python3 \
        python3-venv

RUN python3 -m venv ./.virtualenv

ENV PATH="/app/.virtualenv/bin:$PATH"

RUN pip install --no-cache-dir jupyter
RUN ipython kernel install --name "docker-venv"

EXPOSE 8080

ENTRYPOINT [ "jupyter", "notebook", "--allow-root", "--no-browser", "--ip=0.0.0.0", "--port=8080"]
