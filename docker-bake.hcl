group "all" {
    targets = ["jupyter", "app"]
}

target "jupyter" {
    dockerfile = "Dockerfile"
    context = "./docker/jupyter-base"
    tags = ["jupyter-base:latest"]
}

target "app" {
    dockerfile = "Dockerfile"
    context = "./docker/app"
    tags = ["docling-app"]
    contexts = {
        jupyter-base = "target:jupyter"
    }
}