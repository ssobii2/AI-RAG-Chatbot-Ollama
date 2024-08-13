### Prerequisites

- Python 3.10 or 3.11
- Poetry (Follow this [Poetry installation tutorial](https://python-poetry.org/docs/#installation) to install Poetry on your system)
- Ollama Software (https://ollama.com/)

### Ollama Commands Before Running

1. In CMD/Terminal run the following commands:

    ollama pull llama3.1 (For Chat Bot, Size=4.7GB)

    ollama pull nomic-embed-text (For Embeddings, Size=200+ MB)

### Installation

# MAKE SURE YOU HAVE THE OLLAMA MODELS DOWNLOADED BEFORE RUNNING

1. Install dependencies using Poetry:

   poetry install --no-root

2. Activate the Poetry shell to run:

   poetry shell

3. Run code:

    python ./chatbot.py