// static/js/chatbox.js
document.addEventListener("DOMContentLoaded", () => {
  const chatBox   = document.getElementById("chatbox");
  const chatBody  = document.getElementById("chat-body");
  const chatForm  = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatToggle= document.getElementById("chat-toggle");

  // Nếu không có chatbox trên trang thì thoát luôn (tránh lỗi JS)
  if (!chatBox || !chatBody || !chatForm || !chatInput || !chatToggle) {
    return;
  }

  function appendMsg(text, who) {
    const msg = document.createElement("div");
    msg.className = "msg " + who;   // msg user / msg bot
    msg.textContent = text;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // Gửi tin nhắn
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    appendMsg(text, "user");
    chatInput.value = "";

    try {
      const res = await fetch("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await res.json();
      appendMsg(data.reply || "Xin lỗi, trợ lý đang gặp lỗi.", "bot");
    } catch (err) {
      console.error(err);
      appendMsg("Mạng lỗi hoặc server AI đang tạm thời không phản hồi. Thử lại sau nhé!", "bot");
    }
  });

  // Thu nhỏ / mở rộng chatbox
  chatToggle.addEventListener("click", (e) => {
    e.stopPropagation();
    chatBox.classList.toggle("minimized");
    chatToggle.textContent = chatBox.classList.contains("minimized") ? "+" : "–";
  });
});
