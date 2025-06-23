document.addEventListener('DOMContentLoaded', () => {
const messagesContainer = document.querySelector('.messages');

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

scrollToBottom();

const observer = new MutationObserver(() => {
    scrollToBottom();
});
observer.observe(messagesContainer, { childList: true, subtree: true });

const chatInput = document.querySelector('.chat-input');
chatInput.addEventListener('focus', scrollToBottom);
});
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('chats-search');
    const chatItems = document.querySelectorAll('.chat-item');

    function updateRoundedBorders() {
  const visibleItems = [...document.querySelectorAll('.chat-item')]
    .filter(item => item.style.display !== 'none');
  
    visibleItems.forEach(item => {
      item.style.borderBottomLeftRadius = '0';
      item.style.borderBottomRightRadius = '0';
    });

    if (visibleItems.length > 0) {
      const last = visibleItems[visibleItems.length - 1];
      last.style.borderBottomLeftRadius = '0.5rem';
      last.style.borderBottomRightRadius = '0.5rem';
    }
  }

  searchInput.addEventListener('input', () => {
    const filter = searchInput.value.toLowerCase();

    chatItems.forEach(item => {
      const firstName = item.getAttribute('data-first-name') || '';
      const lastName = item.getAttribute('data-last-name') || '';
      const username = item.getAttribute('data-username') || '';

      if (
        firstName.includes(filter) ||
        lastName.includes(filter) ||
        username.includes(filter)
      ) {
        item.classList.remove('hidden');
        item.classList.add('visible');
      } else {
        item.classList.remove('visible');
        item.classList.add('hidden');
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