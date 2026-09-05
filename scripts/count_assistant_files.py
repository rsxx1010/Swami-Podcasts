import os
import re

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
assistant_name = os.environ.get("PINECONE_ASSISTANT_NAME", "swami-podcasts")

files = pc.assistants.list_files(assistant_name=assistant_name).to_list()
no_dupes = set(file.name for file in files)


def file_sort_key(file):
    """Sort Bhagavad Gita files before Upanishad files, by episode number."""
    match = re.match(r"^(BG|UP)(\d+)", file.name, re.IGNORECASE)
    if match:
        prefix, number = match.groups()
        collection_order = {"BG": 0, "UP": 1}
        return (collection_order[prefix.upper()], int(number), file.name.casefold())

    return (2, 0, file.name.casefold())

print(f"Assistant: {assistant_name}")
print(f"File count: {len(files)}")

for file in sorted(files, key=file_sort_key):
    print(f"- {file.name}")

if len(files) == len(no_dupes):
    print("THERE ARE NO DUPLICATE FILES")
else:
    print("THERE IS A DUPLICATE FILE")