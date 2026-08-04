#uploads all files

from pathlib import Path
from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
assistant_name = os.environ.get("PINECONE_ASSISTANT_NAME", "swami-podcasts")

for path in Path("transcripts").glob("*/*.txt"):
    uploaded = pc.assistants.upload_file(
        assistant_name=assistant_name,
        file_path=str(path),
        metadata={
            "collection": path.parent.name,
            "file_name": path.name,
        },
        timeout=None,
    )
    print(f"Uploaded {path} -> {uploaded.name}")