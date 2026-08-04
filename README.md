# Swami Podcasts Chat

A retrieval-augmented chat site for Bhagavad Gita and Upanishad podcast transcripts. Pinecone Assistant retrieves transcript passages and produces cited answers. FastAPI keeps the Pinecone API key private, while GitHub Pages hosts the frontend.

## Architecture

```text
Browser on GitHub Pages
        |
        | POST /api/chat
        v
FastAPI on Render
        |
        v
Pinecone Assistant and uploaded transcripts
```

The `transcripts/` directory is included in this repository as the source material. Pinecone has its own uploaded copy, which the live chat uses.

## Run locally

Create a `.env` file containing your private configuration:

```env
PINECONE_API_KEY=your_key_here
PINECONE_ASSISTANT_NAME=swami-podcasts
PINECONE_MODEL=gpt-4o-mini
```

Install dependencies and run the app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`.

## Deploy the API to Render

1. Push this repository to GitHub.
2. In Render, create a new **Blueprint** from the GitHub repository. Render reads `render.yaml`.
3. In the Render service's Environment settings, set:
   - `PINECONE_API_KEY` to your real Pinecone key.
   - `ALLOWED_ORIGINS` to `https://YOUR_GITHUB_USERNAME.github.io`.
4. Deploy the service and copy its URL, such as `https://swami-podcasts-api.onrender.com`.

Do not put the Pinecone key in GitHub, the Pages site, or the browser.

## Deploy the frontend to GitHub Pages

1. In the GitHub repository, open **Settings > Pages** and choose **GitHub Actions** as the source.
2. Open **Settings > Secrets and variables > Actions > Variables** and add a repository variable:
   - Name: `API_BASE_URL`
   - Value: the Render URL from the previous section, without a trailing `/`.
3. Push to `main` or run the **Deploy GitHub Pages** workflow from the Actions tab.

The workflow publishes only the static frontend. It injects `API_BASE_URL` into the deployed site so browser requests go to the Render API.

## Upload transcripts

To add transcript files to the Pinecone Assistant:

```bash
python3 scripts/upload_transcripts.py
```

See `scripts/count_assistant_files.py` to list the currently uploaded files.
