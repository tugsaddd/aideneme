/* ============================================================
   Yerel AI – Frontend
   ============================================================ */
"use strict";

// ---------------------------------------------------------------------------
// Durum
// ---------------------------------------------------------------------------
let conversationHistory = [];   // {role, content}[]
let isStreaming = false;
let currentModel = "";

// ---------------------------------------------------------------------------
// DOM referansları
// ---------------------------------------------------------------------------
const messagesEl   = document.getElementById("messages");
const userInput    = document.getElementById("user-input");
const sendBtn      = document.getElementById("send-btn");
const modelSelect  = document.getElementById("model-select");
const systemPrompt = document.getElementById("system-prompt");
const newChatBtn   = document.getElementById("new-chat-btn");
const statusBar    = document.getElementById("status-bar");
const currentModelEl = document.getElementById("current-model");

// ---------------------------------------------------------------------------
// Başlangıç
// ---------------------------------------------------------------------------
(async function init() {
  await checkHealth();
  await loadModels();

  userInput.addEventListener("keydown", handleKey);
  sendBtn.addEventListener("click", sendMessage);
  newChatBtn.addEventListener("click", newChat);
  modelSelect.addEventListener("change", () => {
    currentModel = modelSelect.value;
    if (currentModelEl) currentModelEl.textContent = currentModel;
  });

  autoResizeTextarea(userInput);
})();

// ---------------------------------------------------------------------------
// Sağlık kontrolü
// ---------------------------------------------------------------------------
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.ollama) {
      setStatus("✅ Ollama bağlantısı kuruldu", "ok");
    } else {
      setStatus("⚠️ Ollama çalışmıyor – lütfen başlatın", "error");
    }
  } catch {
    setStatus("⚠️ Sunucuya ulaşılamıyor", "error");
  }
}

function setStatus(msg, cls) {
  statusBar.textContent = msg;
  statusBar.className = `status-bar ${cls}`;
}

// ---------------------------------------------------------------------------
// Model listesi
// ---------------------------------------------------------------------------
async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    const models = data.models;
    const defaultModel = data.default;

    modelSelect.innerHTML = "";

    if (!models || models.length === 0) {
      const opt = document.createElement("option");
      opt.value = defaultModel;
      opt.textContent = defaultModel + " (yüklü değil)";
      modelSelect.appendChild(opt);
      currentModel = defaultModel;
    } else {
      models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        if (m === defaultModel || m.startsWith(defaultModel)) opt.selected = true;
        modelSelect.appendChild(opt);
      });
      currentModel = modelSelect.value;
    }

    if (currentModelEl) currentModelEl.textContent = currentModel;
  } catch {
    currentModel = "llama3.2";
    if (currentModelEl) currentModelEl.textContent = currentModel;
  }
}

// ---------------------------------------------------------------------------
// Mesaj gönderme
// ---------------------------------------------------------------------------
function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isStreaming) return;

  // Kullanıcı mesajını UI'a ekle
  conversationHistory.push({ role: "user", content: text });
  addMessageBubble("user", text);

  userInput.value = "";
  userInput.style.height = "auto";

  // Geçici "yazıyor" balonu
  const aiBubble = addTypingBubble();

  isStreaming = true;
  sendBtn.disabled = true;

  const messages = conversationHistory.map(m => ({ role: m.role, content: m.content }));
  const sysMsg = systemPrompt.value.trim() || undefined;

  let fullReply = "";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages,
        model: currentModel,
        stream: true,
        system_prompt: sysMsg,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "İstek başarısız");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value, { stream: true }).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const jsonStr = line.slice(5).trim();
        if (!jsonStr) continue;

        let chunk;
        try { chunk = JSON.parse(jsonStr); } catch { continue; }

        if (chunk.error) {
          aiBubble.textContent = `Hata: ${chunk.error}`;
          break;
        }

        if (chunk.content) {
          fullReply += chunk.content;
          aiBubble.textContent = fullReply;
          scrollToBottom();
        }

        if (chunk.done) break;
      }
    }

    conversationHistory.push({ role: "assistant", content: fullReply });
  } catch (err) {
    aiBubble.textContent = `❌ Hata: ${err.message}`;
  } finally {
    isStreaming = false;
    sendBtn.disabled = false;
    userInput.focus();
    scrollToBottom();
  }
}

// ---------------------------------------------------------------------------
// UI yardımcıları
// ---------------------------------------------------------------------------
function addMessageBubble(role, text) {
  // Karşılama ekranını kaldır
  const welcome = messagesEl.querySelector(".welcome");
  if (welcome) welcome.remove();

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "👤" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return bubble;
}

function addTypingBubble() {
  const welcome = messagesEl.querySelector(".welcome");
  if (welcome) welcome.remove();

  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";
  wrapper.id = "typing-wrapper";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML =
    '<span class="typing-dot">●</span>' +
    '<span class="typing-dot">●</span>' +
    '<span class="typing-dot">●</span>';

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return bubble;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function newChat() {
  conversationHistory = [];
  messagesEl.innerHTML = `
    <div class="welcome">
      <h2>Merhaba! 👋</h2>
      <p>Sohbete başlamak için bir şeyler yazın.</p>
      <p class="hint">Model: <strong id="current-model"></strong></p>
    </div>`;
  const modelEl = messagesEl.querySelector("#current-model");
  if (modelEl) modelEl.textContent = currentModel;
  userInput.focus();
}

function autoResizeTextarea(el) {
  el.addEventListener("input", () => {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  });
}
