const USERNAME_KEY = "gem_username";

const usernameOverlay = document.getElementById("username-overlay");
const usernameInput = document.getElementById("username-input");
const usernameSubmit = document.getElementById("username-submit");
const currentUserLabel = document.getElementById("current-user");
const changeUserBtn = document.getElementById("change-user-btn");
const chatWindow = document.getElementById("chat-window");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const attachBtn = document.getElementById("attach-btn");
const fileInput = document.getElementById("file-input");

function getUsername() {
  return localStorage.getItem(USERNAME_KEY);
}

function setUsername(name) {
  localStorage.setItem(USERNAME_KEY, name);
}

function showChatUI() {
  const username = getUsername();
  usernameOverlay.classList.add("hidden");
  currentUserLabel.textContent = username ? `Conectat ca ${username}` : "";
  messageInput.disabled = false;
  sendBtn.disabled = false;
  attachBtn.disabled = false;
  messageInput.focus();
}

function showUsernamePrompt() {
  usernameOverlay.classList.remove("hidden");
  messageInput.disabled = true;
  sendBtn.disabled = true;
  attachBtn.disabled = true;
  usernameInput.value = "";
  usernameInput.focus();
}

usernameSubmit.addEventListener("click", () => {
  const name = usernameInput.value.trim();
  if (!name) return;
  setUsername(name);
  showChatUI();
});

usernameInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") usernameSubmit.click();
});

changeUserBtn.addEventListener("click", () => {
  localStorage.removeItem(USERNAME_KEY);
  chatWindow.innerHTML = "";
  showUsernamePrompt();
});

// --- Message rendering -------------------------------------------------

function createRow(role) {
  const row = document.createElement("div");
  const rowRole = role === "error" ? "error-row" : role;
  row.className = `message-row ${rowRole}`;

  if (role === "user" || role === "assistant") {
    const avatar = document.createElement("div");
    avatar.className = `avatar-tiny ${role}`;
    avatar.textContent = role === "user"
      ? (getUsername() || "?").charAt(0).toUpperCase()
      : "🎓";
    row.appendChild(avatar);
  }

  const col = document.createElement("div");
  col.className = "bubble-col";
  row.appendChild(col);

  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return col;
}

function addBubble(role, text) {
  const col = createRow(role);
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role === "error" ? "error" : role}`;
  bubble.textContent = text;
  col.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

function addThinkingBlock(col, beforeEl, reasoningText) {
  const block = document.createElement("details");
  block.className = "think-block";

  const summary = document.createElement("summary");
  summary.textContent = "Raționament";
  block.appendChild(summary);

  const content = document.createElement("div");
  content.className = "think-content";
  content.textContent = reasoningText;
  block.appendChild(content);

  col.insertBefore(block, beforeEl);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return block;
}

function typingDots() {
  const dots = document.createElement("div");
  dots.className = "typing-dots";
  dots.innerHTML = "<span></span><span></span><span></span>";
  return dots;
}

// --- Sending / receiving -------------------------------------------------

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;

  addBubble("user", text);
  messageInput.value = "";
  messageInput.style.height = "auto";
  sendBtn.disabled = true;

  const col = createRow("assistant");
  const bubble = document.createElement("div");
  bubble.className = "bubble assistant";
  bubble.appendChild(typingDots());
  col.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  let receivedContent = false;

  try {
    const response = await fetch("/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": getUsername(),
      },
      body: JSON.stringify({
        model: "gem-agent",
        stream: true,
        messages: [{ role: "user", content: text }],
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server a răspuns cu status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const event of events) {
        const line = event.trim();
        if (!line.startsWith("data:")) continue;
        const data = line.slice(5).trim();
        if (data === "[DONE]") continue;

        const chunk = JSON.parse(data);
        const delta = chunk.choices?.[0]?.delta;
        if (!delta) continue;

        if (delta.reasoning) {
          addThinkingBlock(col, bubble, delta.reasoning);
        }

        if (delta.content) {
          if (!receivedContent) {
            bubble.textContent = "";
            receivedContent = true;
          }
          bubble.textContent += delta.content;
          chatWindow.scrollTop = chatWindow.scrollHeight;
        }
      }
    }

    if (!receivedContent) bubble.textContent = "";
  } catch (err) {
    bubble.className = "bubble error";
    bubble.textContent = `Eroare: ${err.message}`;
  } finally {
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/upload", {
      method: "POST",
      headers: { "X-User-Id": getUsername() },
      body: formData,
    });
    const data = await response.json();

    if (data.error) {
      addBubble("error", data.error);
      return;
    }
    addBubble(
      "system",
      `📎 Ai încărcat "${data.filename}" (${data.size} bytes). Poți să-i ceri lui Gem să-l citească.`
    );
  } catch (err) {
    addBubble("error", `Eroare la încărcare: ${err.message}`);
  }
}

attachBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) uploadFile(file);
  fileInput.value = "";
});

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = `${messageInput.scrollHeight}px`;
});

if (getUsername()) {
  showChatUI();
} else {
  showUsernamePrompt();
}
