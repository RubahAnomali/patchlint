FROM debian:12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN apt update && apt -y install --no-install-recommends git
RUN apt-get upgrade -y
RUN echo apt-get update # just a note about apt-get update
CMD ["bash"]
