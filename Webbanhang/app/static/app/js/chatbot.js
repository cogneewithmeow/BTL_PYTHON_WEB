(function () {
  const STORAGE_KEY = "alg_chatbot_v1";
  const MAX_HISTORY_TO_SEND = 12;
  const CHAT_ENDPOINT = "/api/chat/";

  function getCookie(name) {
    if (!document.cookie) return null;
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }

  function getCsrfToken() {
    // Primary: cookie `csrftoken` (yêu cầu của backend @csrf_protect)
    const fromCookie = getCookie("csrftoken");
    if (fromCookie) return fromCookie;

    // Fallback: token trong DOM (base.html có hidden csrf form)
    const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : null;
  }

  async function sendChatMessage(message, history) {
    const csrftoken = getCsrfToken();
    if (!csrftoken) {
      throw new Error("Đã có lỗi xảy ra, vui lòng thử lại");
    }

    const res = await fetch(CHAT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ message, history }),
    });

    const data = await res.json().catch(() => null);
    if (!res.ok || !data || !data.ok) {
      throw new Error((data && data.error) || "Đã có lỗi xảy ra, vui lòng thử lại");
    }

    return data.reply;
  }

  function safeJsonParse(text, fallback) {
    try {
      return JSON.parse(text);
    } catch (e) {
      return fallback;
    }
  }

  function nowTs() {
    return new Date().toISOString();
  }

  function clampHistory(messages) {
    const trimmed = Array.isArray(messages) ? messages.slice(-MAX_HISTORY_TO_SEND) : [];
    return trimmed
      .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
      .map((m) => ({ role: m.role, content: m.content }));
  }

  function scrollToBottom(el) {
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function buildMessageEl(msg) {
    const wrap = document.createElement("div");
    wrap.className = `ai-msg ai-msg--${msg.role === "user" ? "user" : "ai"}`;

    const bubble = document.createElement("div");
    bubble.className = "ai-msg__bubble";
    if (msg && msg._error) bubble.classList.add("ai-msg__bubble--error");
    bubble.innerHTML = escapeHtml(msg.content);

    const meta = document.createElement("div");
    meta.className = "ai-msg__meta";
    meta.textContent = msg.role === "user" ? "Bạn" : "AI";

    const inner = document.createElement("div");
    inner.appendChild(bubble);
    inner.appendChild(meta);
    wrap.appendChild(inner);
    return wrap;
  }

  function loadState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    const data = safeJsonParse(raw, null);
    if (!data || typeof data !== "object") return null;
    if (!Array.isArray(data.messages)) return null;
    return {
      isOpen: !!data.isOpen,
      messages: data.messages
        .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
        .slice(-50),
    };
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // ignore quota errors
    }
  }

  function init() {
    const root = document.querySelector("[data-ai-chatbot-root]");
    if (!root) return;

    const btn = root.querySelector("[data-ai-chatbot-btn]");
    const panel = root.querySelector("[data-ai-chatbot-panel]");
    const closeBtn = root.querySelector("[data-ai-chatbot-close]");
    const resetBtn = root.querySelector("[data-ai-chatbot-reset]");
    const messagesEl = root.querySelector("[data-ai-chatbot-messages]");
    const emptyEl = root.querySelector("[data-ai-chatbot-empty]");
    const input = root.querySelector("[data-ai-chatbot-input]");
    const sendBtn = root.querySelector("[data-ai-chatbot-send]");
    const statusEl = root.querySelector("[data-ai-chatbot-status]");

    let state = {
      isOpen: false,
      messages: [],
      isLoading: false,
      error: "",
    };

    const loaded = loadState();
    if (loaded) {
      state.isOpen = loaded.isOpen;
      state.messages = loaded.messages;
    }

    function setOpen(isOpen) {
      state.isOpen = !!isOpen;
      root.classList.toggle("is-open", state.isOpen);
      btn.setAttribute("aria-expanded", state.isOpen ? "true" : "false");
      panel.setAttribute("aria-hidden", state.isOpen ? "false" : "true");
      saveState({ isOpen: state.isOpen, messages: state.messages });
      if (state.isOpen) {
        setTimeout(() => {
          input && input.focus();
          scrollToBottom(messagesEl);
        }, 60);
      }
    }

    function setLoading(isLoading) {
      state.isLoading = !!isLoading;
      sendBtn.disabled = state.isLoading;
      sendBtn.setAttribute("aria-disabled", state.isLoading ? "true" : "false");
      input.disabled = state.isLoading;
      if (!state.isLoading) return;
      setStatusLoading(true);
    }

    function setStatus(text, isError) {
      if (!statusEl) return;
      statusEl.classList.toggle("is-error", !!isError);
      statusEl.textContent = text || "";
    }

    function setStatusLoading(isLoading) {
      if (!statusEl) return;
      if (!isLoading) {
        statusEl.classList.remove("is-error");
        statusEl.innerHTML = "";
        return;
      }
      statusEl.classList.remove("is-error");
      statusEl.innerHTML =
        '<span class="ai-typing">AI đang trả lời <span class="ai-dots" aria-hidden="true"><span></span><span></span><span></span></span></span>';
    }

    function render() {
      messagesEl.innerHTML = "";
      if (state.messages.length === 0) {
        emptyEl.style.display = "";
      } else {
        emptyEl.style.display = "none";
        for (const m of state.messages) {
          messagesEl.appendChild(buildMessageEl(m));
        }
      }
      scrollToBottom(messagesEl);
      saveState({ isOpen: state.isOpen, messages: state.messages });
    }

    async function sendMessage() {
      const raw = input.value || "";
      const message = raw.trim();
      if (!message) return;
      if (state.isLoading) return;

      state.error = "";
      setStatus("", false);

      state.messages.push({ role: "user", content: message, ts: nowTs() });
      input.value = "";
      render();

      setLoading(true);

      // Hiển thị bubble "đang trả lời" để user không thấy bị đứng
      const pendingIndex = state.messages.push({ role: "assistant", content: "AI đang trả lời…", ts: nowTs(), _pending: true }) - 1;
      render();

      try {
        const reply = await sendChatMessage(message, clampHistory(state.messages));
        if (typeof reply !== "string" || !reply.trim()) {
          throw new Error("Đã có lỗi xảy ra, vui lòng thử lại");
        }

        // Replace pending bubble (nếu có) bằng reply thật
        if (state.messages[pendingIndex] && state.messages[pendingIndex]._pending) {
          state.messages[pendingIndex] = { role: "assistant", content: reply, ts: nowTs() };
        } else {
          state.messages.push({ role: "assistant", content: reply, ts: nowTs() });
        }
        render();
        setStatus("", false);
      } catch (err) {
        const friendly = err && err.message ? String(err.message) : "Đã có lỗi xảy ra, vui lòng thử lại";
        state.error = friendly;
        setStatus(state.error, true);

        // Hiển thị lỗi ngay trong khung chat (thay pending bubble)
        if (state.messages[pendingIndex] && state.messages[pendingIndex]._pending) {
          state.messages[pendingIndex] = { role: "assistant", content: friendly, ts: nowTs(), _error: true };
        } else {
          state.messages.push({ role: "assistant", content: friendly, ts: nowTs(), _error: true });
        }
        render();
      } finally {
        setLoading(false);
        setStatusLoading(false);
      }
    }

    function resetChat() {
      if (state.isLoading) return;
      state.messages = [];
      state.error = "";
      setStatus("", false);
      render();
      input && input.focus();
    }

    btn.addEventListener("click", function () {
      setOpen(!state.isOpen);
    });
    closeBtn.addEventListener("click", function () {
      setOpen(false);
    });
    resetBtn.addEventListener("click", function () {
      resetChat();
    });
    sendBtn.addEventListener("click", function () {
      sendMessage();
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Close when clicking outside (desktop)
    document.addEventListener("click", function (e) {
      if (!state.isOpen) return;
      const target = e.target;
      if (!target || !(target instanceof Element)) return;
      if (root.contains(target)) return;
      setOpen(false);
    });

    // Esc closes
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && state.isOpen) {
        setOpen(false);
      }
    });

    // initial
    setOpen(state.isOpen);
    setLoading(false);
    setStatusLoading(false);
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

