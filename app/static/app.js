const form = document.querySelector("#chat-form");
const result = document.querySelector("#result");
const answer = document.querySelector("#answer");
const citations = document.querySelector("#citations");
const button = form.querySelector("button");
const apiBaseUrl = (window.SWAMI_API_BASE_URL || "").replace(/\/$/, "");

function chatEndpoint() {
  if (!apiBaseUrl && window.location.hostname.endsWith("github.io")) {
    throw new Error("This Pages site is not connected to its chat server yet.");
  }

  return `${apiBaseUrl}/api/chat`;
}

function renderCitations(items) {
  citations.innerHTML = "";

  if (!items.length) {
    citations.textContent = "No citations returned.";
    return;
  }

  const heading = document.createElement("h3");
  heading.textContent = "Sources";
  citations.appendChild(heading);

  const list = document.createElement("ul");
  for (const item of items) {
    const row = document.createElement("li");
    const source = [item.collection, item.file_name].filter(Boolean).join(" / ");
    const title = document.createElement("strong");
    title.textContent = source || "Unknown source";
    row.appendChild(title);

    if (item.highlight) {
      const quote = document.createElement("blockquote");
      quote.textContent = item.highlight;
      row.appendChild(quote);
    }

    list.appendChild(row);
  }

  citations.appendChild(list);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  button.disabled = true;
  button.textContent = "Asking...";
  result.hidden = false;
  answer.textContent = "Searching the uploaded transcripts...";
  citations.innerHTML = "";

  try {
    const response = await fetch(chatEndpoint(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: form.question.value,
        collection: form.collection.value,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    answer.textContent = data.answer;
    renderCitations(data.citations || []);
  } catch (error) {
    answer.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Ask";
  }
});
