# ollama/entrypoint.sh
#!/bin/sh
# Pull the Mistral 7B model on startup (uses the Ollama CLI)
ollama pull mistral
# Start the Ollama API server on all interfaces
exec ollama serve --listen 0.0.0.0 --port 11434
