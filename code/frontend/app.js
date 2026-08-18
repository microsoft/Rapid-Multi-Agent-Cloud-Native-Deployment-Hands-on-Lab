const API_BASE = window.MOODFRAME_API_BASE || "http://localhost:8000";
const moods = [...document.querySelectorAll(".mood")];
const generateButton = document.querySelector("#generate");
const statusLine = document.querySelector("#status");
const result = document.querySelector("#result");
const downloadButton = document.querySelector("#download");
let selected = { mood: "joyful", emoji: "😊" };

moods.forEach((button) => {
  button.addEventListener("click", () => {
    moods.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    selected = { mood: button.dataset.mood, emoji: button.dataset.emoji };
  });
});

generateButton.addEventListener("click", async () => {
  generateButton.disabled = true;
  result.classList.add("hidden");
  statusLine.textContent = "The agents are writing and developing your pixel film...";
  try {
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...selected,
        language: document.querySelector("#language").value,
      }),
    });
    if (!response.ok) {
      const problem = await response.json();
      throw new Error(problem.detail || "Generation failed");
    }
    const data = await response.json();
    document.querySelector("#artwork").src = `${API_BASE}${data.image_url}`;
    document.querySelector("#caption").textContent = data.post.caption;
    document.querySelector("#hashtags").textContent = data.post.hashtags.join(" ");
    downloadButton.href = `${API_BASE}${data.download_url}`;
    downloadButton.download = `moodframe-${selected.mood}.png`;
    result.classList.remove("hidden");
    result.scrollIntoView({ behavior: "smooth", block: "start" });
    statusLine.textContent = "";
  } catch (error) {
    statusLine.textContent = error.message;
  } finally {
    generateButton.disabled = false;
  }
});
