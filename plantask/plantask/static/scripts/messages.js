document.addEventListener('DOMContentLoaded', () => {
  let groupSelected = [];

  const groupUserSearch = document.getElementById('groupUserSearch');
  const groupUserResults = document.getElementById('groupUserResults');
  const chatItems = document.querySelectorAll('.chat-item');
  const messagesContainer = document.querySelector('.messages');
  const chatInfo = document.querySelector('.ChatInfo');
  const chatIdField = document.getElementById('chat-id-field');
  const isPersonalField = document.getElementById('is-personal-chat-field');
  const messageForm = document.getElementById('message-form');
  const messageInput = document.getElementById('message-input');
  const scrollBtn = document.getElementById('scroll-to-bottom-btn');
  const userId = parseInt(document.getElementById('user-data')?.dataset.userId || '0');
  let currentChatId = null;
  let currentChatIsGroup = false;

  // ========== MODAL HANDLING ==========

  document.getElementById('new-chat-btn').addEventListener('click', () => {
    groupSelected = [];
    groupUserSearch.value = '';
    groupUserResults.textContent = '';
    document.getElementById('groupSelectedUsers').innerHTML = "<li class='text-muted list-group-item'>No users selected</li>";
    document.getElementById('groupHiddenInputs').textContent = '';
    document.getElementById('createGroupSubmit').disabled = true;
    new bootstrap.Modal(document.getElementById('createGroupModal')).show();
  });

  groupUserSearch.addEventListener('input', async function () {
    const value = this.value.trim();
    if (value.length < 2) return;

    try {
      const res = await fetch(`/search-users-global?q=${encodeURIComponent(value)}`);
      const users = await res.json();

      groupUserResults.textContent = '';
      if (!users.length) {
        groupUserResults.textContent = "No users found";
        return;
      }

      users.forEach(user => {
        if (groupSelected.some(u => u.id === user.id)) return;

        const wrapper = document.createElement('div');
        wrapper.className = "d-flex justify-content-between align-items-center border rounded p-2 mb-2";
        wrapper.innerHTML = `
          <div class="d-flex align-items-center">
            <img src="${user.image_route || '/static/default_pfp.svg'}"
                 class="rounded-circle me-2" style="width: 2.5rem; height: 2.5rem; object-fit: cover;">
            <div>
              <strong>${user.first_name} ${user.last_name}</strong><br>
              <small class="text-muted">@${user.username}</small>
            </div>
          </div>
          <button class="btn btn-sm btn-success ms-2">Add</button>
        `;
        wrapper.querySelector('button').addEventListener('click', () => {
          groupSelected.push(user);
          updateGroupSelected();
          wrapper.remove();
        });
        groupUserResults.appendChild(wrapper);
      });
    } catch (err) {
      console.error("❌ Fetch failed:", err);
      groupUserResults.textContent = "Error fetching users";
    }
  });

  function updateGroupSelected() {
    const list = document.getElementById('groupSelectedUsers');
    const hidden = document.getElementById('groupHiddenInputs');
    const submit = document.getElementById('createGroupSubmit');

    list.innerHTML = '';
    hidden.innerHTML = '';

    if (!groupSelected.length) {
      list.innerHTML = "<li class='text-muted list-group-item'>No users selected</li>";
      submit.disabled = true;
      return;
    }

    groupSelected.forEach(u => {
      const li = document.createElement('li');
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      li.innerHTML = `
        <div><strong>${u.first_name} ${u.last_name}</strong> <small class="text-muted">@${u.username}</small></div>
        <button class="btn btn-sm btn-outline-danger">Remove</button>
      `;
      li.querySelector('button').addEventListener('click', () => {
        groupSelected = groupSelected.filter(x => x.id !== u.id);
        updateGroupSelected();
      });
      list.appendChild(li);

      const hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';
      hiddenInput.name = 'user_ids';
      hiddenInput.value = u.id;
      hidden.appendChild(hiddenInput);
    });

    submit.disabled = groupSelected.length < 2;
  }

  // ========== CHAT SECTION ==========

  const scrollToBottom = () => {
    messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' });
  };

  const handleScrollButtonVisibility = () => {
    const threshold = 100;
    const atBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold;
    scrollBtn.style.display = atBottom ? 'none' : 'block';
  };

  scrollBtn.addEventListener('click', scrollToBottom);
  messagesContainer.addEventListener('scroll', handleScrollButtonVisibility);

  function getFriendlyDateLabel(dateObj) {
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    if (dateObj.toDateString() === today.toDateString()) return "Today";
    if (dateObj.toDateString() === yesterday.toDateString()) return "Yesterday";
    return dateObj.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }

  const renderMessages = (messages) => {
    chatInfo.classList.remove('d-none');
    messageForm.classList.remove('d-none');
    messagesContainer.innerHTML = "";

    if (!messages.length) {
      messagesContainer.innerHTML = '<p style="text-align:center; color:#aaa;">No messages yet</p>';
      return;
    }

    let lastRenderedDate = null;

    messages.forEach(msg => {
      const dateObj = new Date(msg.date_sent);
      const dateLabel = getFriendlyDateLabel(dateObj);
      const hora = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      if (dateLabel !== lastRenderedDate) {
        const dateDivider = document.createElement('div');
        dateDivider.className = "date-divider text-muted my-2";
        dateDivider.textContent = dateLabel;
        messagesContainer.appendChild(dateDivider);
        lastRenderedDate = dateLabel;
      }

      const msgWrapper = document.createElement('div');
      msgWrapper.className = msg.sender_id === userId ? 'mymessage' : 'amessage';

      msgWrapper.innerHTML = `
        <p class="message-info">${hora}</p>
        <p class="${msg.sender_id === userId ? 'mymessagebubble' : 'amessagebubble'}">${msg.message_cont}</p>
        ${msg.sender_id === userId ? `<i class="bi ${msg.state === 'read' ? 'bi-check2-all' : 'bi-check2'}"></i>` : ''}
      `;

      messagesContainer.appendChild(msgWrapper);
    });

    scrollToBottom();
    handleScrollButtonVisibility();
  };

  const fetchAndRenderMessages = async (chatId, isGroup = false) => {
    try {
      const endpoint = isGroup ? `/get-group-chat-messages/${chatId}` : `/get-chat-messages/${chatId}`;
      const res = await fetch(endpoint);
      const data = await res.json();
      
      if (isGroup) {
        renderGroupMessages(data.messages || [], data.chat_name || 'Group Chat');
      } else {
        renderMessages(data.messages || []);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      messagesContainer.innerHTML = '<p class="text-center text-danger">Error loading messages</p>';
    }
  };

  // Update chat item click handler
  chatItems.forEach(item => {
    item.addEventListener('click', async () => {
      chatItems.forEach(el => el.classList.remove('active'));
      item.classList.add('active');

      const { chatId, firstName, lastName, username, imageRoute, otherUserId } = item.dataset;
      const isGroup = item.dataset.isGroup === 'true';
      
      currentChatId = chatId;
      currentChatIsGroup = isGroup;
      chatIdField.value = chatId;
      isPersonalField.value = isGroup ? 'false' : 'true';
      
      // Clear existing messages
      messagesContainer.innerHTML = '<p class="text-center">Loading messages...</p>';

      if (isGroup) {
        // Group chat display
        chatInfo.querySelector('.chatinfo-pfp').src = imageRoute || "/static/default_pfp.svg";
        chatInfo.querySelector('h4').textContent = firstName;
        chatInfo.querySelector('a').textContent = "Group Chat";
        
        // Fetch group messages using unified function
        await fetchAndRenderMessages(chatId, true);
      } else {
        // Personal chat display
        const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
        chatInfo.querySelector('.chatinfo-pfp').src = imageRoute || "/static/default_pfp.svg";
        chatInfo.querySelector('h4').textContent = `${cap(firstName)} ${cap(lastName)}`;
        chatInfo.querySelector('a').textContent = `@${username}`;
        
        // Set profile click handlers for personal chats
        ['.chatinfo-pfp', 'h4', 'a'].forEach(selector => {
          chatInfo.querySelector(selector).onclick = () => window.location.href = `/user/${otherUserId}`;
        });
        
        // Fetch personal messages using unified function
        await fetchAndRenderMessages(chatId, false);
      }
      
      chatInfo.classList.remove('d-none');
      messageForm.classList.remove('d-none');
    });
  });
  
  // Add this new function for rendering group messages
  const renderGroupMessages = (messages, groupName) => {
    messagesContainer.innerHTML = "";

    if (!messages.length) {
      messagesContainer.innerHTML = '<p style="text-align:center; color:#aaa;">No messages yet in this group</p>';
      return;
    }

    let lastRenderedDate = null;

    messages.forEach(msg => {
      const dateObj = new Date(msg.date_sent);
      const dateLabel = getFriendlyDateLabel(dateObj);
      const hora = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      if (dateLabel !== lastRenderedDate) {
        const dateDivider = document.createElement('div');
        dateDivider.className = "date-divider text-muted my-2";
        dateDivider.textContent = dateLabel;
        messagesContainer.appendChild(dateDivider);
        lastRenderedDate = dateLabel;
      }

      const msgWrapper = document.createElement('div');
      msgWrapper.className = msg.sender_id === userId ? 'mymessage' : 'amessage';

      // For group chats, show sender name for messages from others
      const senderInfo = msg.sender_id === userId ? '' : 
        `<small class="sender-name text-muted">${msg.sender_name}</small>`;

      msgWrapper.innerHTML = `
        <p class="message-info">${hora}</p>
        ${senderInfo}
        <p class="${msg.sender_id === userId ? 'mymessagebubble' : 'amessagebubble'}">${msg.message_cont}</p>
        ${msg.sender_id === userId ? `<i class="bi ${msg.state === 'read' ? 'bi-check2-all' : 'bi-check2'}"></i>` : ''}
      `;

      messagesContainer.appendChild(msgWrapper);
    });

    scrollToBottom();
    handleScrollButtonVisibility();
  };

  const urlParams = new URLSearchParams(window.location.search);
  const initialChatId = urlParams.get('currentChatId');
  if (initialChatId) {
    const target = [...chatItems].find(i => i.dataset.chatId === initialChatId);
    if (target) {
      // Set the global variables before clicking
      currentChatId = initialChatId;
      currentChatIsGroup = target.dataset.isGroup === 'true';
      target.click();
    }
  } else {
    chatInfo.classList.add('d-none');
    messageForm.classList.add('d-none');
    messagesContainer.innerHTML = '<p class="text-center text-muted mt-4">Select a chat to view messages</p>';
  }

  setInterval(() => {
    if (!currentChatId) return;
    const distanceFromBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight;
    if (distanceFromBottom < 100) {
      fetchAndRenderMessages(currentChatId, currentChatIsGroup);
    }
  }, 3000);

  messageForm.addEventListener('submit', async e => {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;

    try {
      const formData = new FormData(messageForm);
      const res = await fetch('/send-message', { method: 'POST', body: formData });
      const data = await res.json();

      if (data.success) {
        messageInput.value = '';
        await fetchAndRenderMessages(currentChatId, currentChatIsGroup);
      } else {
        console.error('Send error:', data.error_ping || 'Unknown error');
      }
    } catch (err) {
      console.error('Send failed:', err);
    }
  });
});