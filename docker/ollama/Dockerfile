# ollama/Dockerfile
FROM ollama/ollama:latest

# Copy a custom entrypoint to pull the Mistral model and start the server
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Override entrypoint: pull model then run Ollama server
ENTRYPOINT ["/entrypoint.sh"]
