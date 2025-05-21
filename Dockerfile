FROM jupyter-base

RUN pip install --no-cache-dir \
    docling \
    json-repair \
    llama-index \
    llama-index-llms-ollama