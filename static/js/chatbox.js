document.addEventListener('DOMContentLoaded', () => {
  const chatBody  = document.getElementById('chat-body');
  const chatForm  = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatToggle= document.getElementById('chat-toggle');

  function appendMsg(text, who) {
    const msg = document.createElement('div');
    msg.className = 'msg ' + who;
    msg.textContent = text;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // Gửi tin
  chatForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    appendMsg(text, 'user');
    chatInput.value = '';

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      appendMsg(data.reply || 'Lỗi hệ thống', 'bot');
    } catch {
      appendMsg('Mạng lỗi, thử lại nhé!', 'bot');
    }
  });

  // Thu nhỏ / mở rộng – lấy đúng khối chatbox chứa nút
  chatToggle?.addEventListener('click', (e) => {
    e.stopPropagation();
    const chatBox = chatToggle.closest('#chatbox');   // <-- quan trọng
    chatBox.classList.toggle('minimized');
    chatToggle.textContent = chatBox.classList.contains('minimized') ? '+' : '–';
  });
});
