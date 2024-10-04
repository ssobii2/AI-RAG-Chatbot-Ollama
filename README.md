### Prerequisites

- Docker Desktop

- Run below commands when Docker Desktop is Running then follow below
```
docker buildx build -f Dockerfile.whisper -t whisper-base .
```
- Make sure to run the above command in the backend directory where the Dockerfile.whisper is present. This command will take a lot of time because it will download the full openai-whisper package.

```
docker compose up --build
```
- Make sure to run the above command in the root directory of the project, where the docker-compose.yml file is present.

## Note

When running the first time, the below commands will need to run in the Ollama Container (make sure all the containers or just the ollama container is running) to download the models. I could not find a way to automate this process hence it needs to run manually. The backend will fail because it would not find the models for the first time.

### Ollama Commands After running the Ollama Container

1. In Docker Desktop, click on the Ollama container then go to Exec tab and run the following commands:

    - For Embeddings,
    ```
    ollama pull mxbai-embed-large
    ```
    ### OR
    ```
    ollama pull nomic-embed-text
    ```
    - For Chat Bot,
    ```
    ollama pull llama3.1
    ```
    - For Images
    ```
    ollama pull llava-llama3
    ```
    ### OR
    ```
    ollama pull llava
    ```

2. Which ever model you decided to download, make sure to change it in the chatbot.py file to which ever you downloaded. Search for this comment "# Change to your pulled model" to find where to change.

2. The downloading can also fail due to some reasons so just run the commands again to download them.

3. After running the above commands please check if the db folder in the backend is empty and there are no files because if there are then those vector store files are incorrect and needs to be deleted (It should be empty but just in case please check. To delete them you need to stop the backend container if running)

4. One other thing, backend takes a while to make vector store and download the whisper model so please be patient check the logs for progress and reload the front end page when the backend is fully started. You can check in dev tools network tab to see if its connected to the backend successfully.
