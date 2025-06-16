document.addEventListener('DOMContentLoaded', () => {
const messagesContainer = document.querySelector('.messages');

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Scroll to the bottom on page load
scrollToBottom();

// Scroll to the bottom when new messages are added
const observer = new MutationObserver(() => {
    scrollToBottom();
});
observer.observe(messagesContainer, { childList: true, subtree: true });

// Optional: Scroll to the bottom when the input field is focused
const chatInput = document.querySelector('.chat-input');
chatInput.addEventListener('focus', scrollToBottom);
});
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('chats-search');
    const chatItems = document.querySelectorAll('.chat-item');

    function updateRoundedBorders() {
  const visibleItems = [...document.querySelectorAll('.chat-item')]
    .filter(item => item.style.display !== 'none');
  
    // Quitar borde redondeado a todos
    visibleItems.forEach(item => {
      item.style.borderBottomLeftRadius = '0';
      item.style.borderBottomRightRadius = '0';
    });

    // Aplicar borde redondeado solo al último visible
    if (visibleItems.length > 0) {
      const last = visibleItems[visibleItems.length - 1];
      last.style.borderBottomLeftRadius = '0.5rem';
      last.style.borderBottomRightRadius = '0.5rem';
    }
  }

  // Modifica tu listener de búsqueda así:

  searchInput.addEventListener('input', () => {
    const filter = searchInput.value.toLowerCase();

    chatItems.forEach(item => {
      const firstName = item.getAttribute('data-first-name');
      const lastName = item.getAttribute('data-last-name');
      const username = item.getAttribute('data-username');

      if (
        firstName.includes(filter) || 
        lastName.includes(filter) || 
        username.includes(filter)
      ) {
        item.style.display = 'flex'; // Mostrar
      } else {
        item.style.display = 'none'; // Ocultar
      }
    });

    updateRoundedBorders();
  });
});
document.addEventListener('DOMContentLoaded', () => {
    const chatItems = document.querySelectorAll('.chat-item');

    chatItems.forEach(item => {
      item.addEventListener('click', () => {
        chatItems.forEach(chat => chat.classList.remove('active'));
        item.classList.add('active');
      });
    });
  });