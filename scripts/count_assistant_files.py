import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
assistant_name = os.environ.get("PINECONE_ASSISTANT_NAME", "swami-podcasts")

files = pc.assistants.list_files(assistant_name=assistant_name).to_list()
no_dupes = set(file.name for file in files)

print(f"Assistant: {assistant_name}")
print(f"File count: {len(files)}")

for file in files:
    print(f"- {file.name} ({file.status})")

if len(files) == len(no_dupes):
    print("THERE ARE NO DUPLICATE FILES")
else:
    print("THERE IS A DUPLICATE FILE")