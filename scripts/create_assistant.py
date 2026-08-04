import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

assistant = pc.assistant.create_assistant(
    assistant_name=os.environ["PINECONE_ASSISTANT_NAME"],
    instructions=(
        "Answer only using the uploaded podcast transcripts."
        "When asked for a quote, return an exact excerpt and cite the source file."
        "Do not invent quotes."
        "Use quotes that actually make sense."
    ),
    region="us",
    timeout=30,
)

print(f"Created assistant: {assistant}")