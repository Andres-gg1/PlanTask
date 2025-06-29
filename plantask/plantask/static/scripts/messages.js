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
  let lastMessageCount = 0;
  let isCurrentlyFetching = false;

  // Modal handling

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
      const res = await fetch(`/search-global?q=${encodeURIComponent(value)}`);
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

  // Chat section

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
    // Ensure chat UI elements are visible
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

  const fetchAndRenderMessages = async (chatId, isGroup = false, includeSidebar = false) => {
    // Prevent multiple simultaneous requests for the same chat
    if (isCurrentlyFetching && currentChatId === chatId) {
      return;
    }
    
    isCurrentlyFetching = true;
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const endpoint = isGroup ? `/get-group-chat-messages/${chatId}` : `/get-chat-messages/${chatId}`;
      const res = await fetch(endpoint, { 
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache',
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      
      if (isGroup) {
        const messages = data.messages || [];
        // Only re-render if message count changed or it's initial load
        if (includeSidebar || messages.length !== lastMessageCount) {
          renderGroupMessages(messages, data.chat_name || 'Group Chat');
          lastMessageCount = messages.length;
        }
        
        // Only populate sidebar when explicitly requested
        if (includeSidebar) {
          populateGroupSidebar({
            chat_name: data.chat_name,
            description: data.description,
            image_route: data.image_route,
            creation_date: data.creation_date,
            members: data.members
          });
        }
      } else {
        const messages = data.messages || [];
        // Only re-render if message count changed or it's initial load
        if (includeSidebar || messages.length !== lastMessageCount) {
          renderMessages(messages);
          lastMessageCount = messages.length;
        }
      }
    } catch (err) {
      // Ensure UI is visible even on error
      chatInfo.classList.remove('d-none');
      messageForm.classList.remove('d-none');
      messagesContainer.innerHTML = '<p class="text-center text-danger">Error loading messages</p>';
    } finally {
      isCurrentlyFetching = false;
    }
  };

  // Sidebar functionality
  const groupOptionsBtn = document.getElementById('group-options-btn');
  const groupInfoSidebar = document.getElementById('group-info-sidebar');
  const closeSidebarBtn = document.getElementById('close-sidebar-btn');
  const groupMembersList = document.getElementById('group-members-list');

  const showGroupSidebar = () => {
    groupInfoSidebar.classList.remove('d-none');
    groupInfoSidebar.classList.add('show');
    messagesContainer.classList.add('sidebar-open');
    document.querySelector('.ChatInfo').classList.add('sidebar-open');
    document.querySelector('.chat-input-bar').classList.add('sidebar-open');
  };

  const hideGroupSidebar = () => {
    groupInfoSidebar.classList.remove('show');
    messagesContainer.classList.remove('sidebar-open');
    document.querySelector('.ChatInfo').classList.remove('sidebar-open');
    document.querySelector('.chat-input-bar').classList.remove('sidebar-open');
    setTimeout(() => {
      groupInfoSidebar.classList.add('d-none');
    }, 300);
  };

  groupOptionsBtn.addEventListener('click', showGroupSidebar);
  closeSidebarBtn.addEventListener('click', hideGroupSidebar);

  // Close sidebar when clicking outside
  document.addEventListener('click', (e) => {
    if (!groupInfoSidebar.contains(e.target) && 
        !groupOptionsBtn.contains(e.target) && 
        groupInfoSidebar.classList.contains('show')) {
      hideGroupSidebar();
    }
  });

  const populateGroupSidebar = (groupData) => {
    document.querySelector('.group-avatar').src = groupData.image_route || '/static/default_pfp.svg';
    document.querySelector('.group-name').textContent = groupData.chat_name || 'Group Chat';
    document.querySelector('.group-description').textContent = groupData.description || 'No description available';
    document.getElementById('group-creation-date').textContent = new Date(groupData.creation_date).toLocaleDateString();

    groupMembersList.innerHTML = '';

    if (groupData.members && groupData.members.length > 0) {
      groupData.members.forEach(member => {
        const memberItem = document.createElement('div');
        memberItem.className = 'member-item d-flex justify-content-between align-items-center mb-2';

        const memberInfo = document.createElement('div');
        memberInfo.className = 'd-flex align-items-center';
        memberInfo.style.cursor = 'pointer';
        memberInfo.innerHTML = `
          <img src="${member.pfp_route || '/static/default_pfp.svg'}" 
              alt="${member.first_name} ${member.last_name}" 
              class="member-avatar me-2">
          <div>
            <p class="member-name mb-0">${member.first_name} ${member.last_name}</p>
            <p class="member-username text-muted mb-0">@${member.username}</p>
          </div>
        `;

        memberInfo.addEventListener('click', () => {
          window.location.href = `/user/${member.user_id}`;
        });

        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn btn-sm btn-outline-danger';
        removeBtn.innerHTML = `<i class="bi bi-x-lg"></i>`;
        removeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          confirmRemoveFromGroup(member.user_id, `${member.first_name} ${member.last_name}`, groupData.chat_name);
        });

        memberItem.appendChild(memberInfo);
        memberItem.appendChild(removeBtn);
        groupMembersList.appendChild(memberItem);
      });
    } else {
      groupMembersList.innerHTML = '<p class="text-muted text-center">No members found</p>';
    }
    };

  // Update chat item click handler
  chatItems.forEach(item => {
    item.addEventListener('click', async () => {
      const { chatId, firstName, lastName, username, imageRoute, otherUserId } = item.dataset;
      const isGroup = item.dataset.isGroup === 'true';
      
      // Don't reload if same chat is selected
      if (currentChatId === chatId && currentChatIsGroup === isGroup) {
        return;
      }
      
      stopMessageRefresh();
      
      chatItems.forEach(el => el.classList.remove('active'));
      item.classList.add('active');
      
      initializeChat(chatId, isGroup);
      chatIdField.value = chatId;
      isPersonalField.value = isGroup ? 'false' : 'true';
      
      hideGroupSidebar();
      
      chatInfo.classList.remove('d-none');
      messageForm.classList.remove('d-none');
      
      messagesContainer.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

      if (isGroup) {
        setCurrentGroupId(chatId);
        
        document.querySelector('.group-options-btn').classList.remove('d-none');
        document.querySelector('.group-indicator').classList.remove('d-none');
        document.querySelector('.user-profile-link').style.display = 'none';
        
        chatInfo.querySelector('.chatinfo-pfp').src = imageRoute || "/static/default_pfp.svg";
        chatInfo.querySelector('h4').textContent = firstName;
        
        ['.chatinfo-pfp', 'h4'].forEach(selector => {
          chatInfo.querySelector(selector).onclick = null;
        });
        
        try {
          await fetchAndRenderMessages(chatId, true, true);
        } catch (error) {
          messagesContainer.innerHTML = '<p class="text-center text-danger">Error loading messages</p>';
        }
      } else {
        setCurrentGroupId(null);
        
        document.querySelector('.group-options-btn').classList.add('d-none');
        document.querySelector('.group-indicator').classList.add('d-none');
        document.querySelector('.user-profile-link').style.display = 'inline';
        
        const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
        chatInfo.querySelector('.chatinfo-pfp').src = imageRoute || "/static/default_pfp.svg";
        chatInfo.querySelector('h4').textContent = `${cap(firstName)} ${cap(lastName)}`;
        chatInfo.querySelector('a').textContent = `@${username}`;
        
        ['.chatinfo-pfp', 'h4', 'a'].forEach(selector => {
          chatInfo.querySelector(selector).onclick = () => window.location.href = `/user/${otherUserId}`;
        });
        
        try {
          await fetchAndRenderMessages(chatId, false, true);
        } catch (error) {
          messagesContainer.innerHTML = '<p class="text-center text-danger">Error loading messages</p>';
        }
      }
    });
  });
  
  // Group message rendering
  const renderGroupMessages = (messages, groupName) => {
    chatInfo.classList.remove('d-none');
    messageForm.classList.remove('d-none');
    
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

      if (msg.sender_id === userId) {
        msgWrapper.innerHTML = `
          <p class="message-info text-end">${hora}</p>
          <p class="mymessagebubble">${msg.message_cont}</p>
          <i class="bi ${msg.state === 'read' ? 'bi-check2-all' : 'bi-check2'}"></i>
        `;
      } else {
        msgWrapper.innerHTML = `
          <div class="text-center">
            <div class="text-muted small mt-1">${hora}</div>
            <div class="message-block d-flex align-items-center justify-content-center">
              <img src="${msg.sender_pfp || '/static/default_pfp.svg'}" class="rounded-circle me-2" style="width: 30px; height: 30px; object-fit: cover;">
              <div class="amessagebubble">${msg.message_cont}</div>
            </div>
            <div class="text-muted small">${msg.sender_name}</div>
          </div>
        `;
      }

      messagesContainer.appendChild(msgWrapper);
    });

    scrollToBottom();
    handleScrollButtonVisibility();
  };

  // Initialize chat if URL parameter exists
  const urlParams = new URLSearchParams(window.location.search);
  const initialChatId = urlParams.get('currentChatId');
  
  if (initialChatId) {
    const target = [...chatItems].find(i => i.dataset.chatId === initialChatId);
    
    if (target) {
      setTimeout(() => {
        if (target && target.isConnected) {
          target.click();
          setTimeout(() => {
            if (chatInfo.classList.contains('d-none')) {
              chatInfo.classList.remove('d-none');
              messageForm.classList.remove('d-none');
            }
          }, 100);
        }
      }, 10);
    } else {
      chatInfo.classList.add('d-none');
      messageForm.classList.add('d-none');
      messagesContainer.innerHTML = '<p class="text-center text-muted mt-4">Chat not found. Select a chat to view messages</p>';
    }
  } else {
    chatInfo.classList.add('d-none');
    messageForm.classList.add('d-none');
    messagesContainer.innerHTML = '<p class="text-center text-muted mt-4">Select a chat to view messages</p>';
  }

  // Optimize performance based on page visibility
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopMessageRefresh();
    } else if (currentChatId) {
      startMessageRefresh();
      fetchAndRenderMessages(currentChatId, currentChatIsGroup, false);
    }
  });

  // Cleanup when leaving page
  window.addEventListener('beforeunload', () => {
    stopMessageRefresh();
  });

  // Periodic refresh with intelligent polling
  let refreshInterval = null;
  
  const startMessageRefresh = () => {
    stopMessageRefresh();
    
    refreshInterval = setInterval(() => {
      if (!currentChatId || isCurrentlyFetching) return;
      
      // Only refresh if user is near bottom of chat
      const distanceFromBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight;
      if (distanceFromBottom < 200) {
        fetchAndRenderMessages(currentChatId, currentChatIsGroup, false);
      }
    }, 3500);
  };
  
  const stopMessageRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  };
  
  // Start refresh when a chat is selected
  const initializeChat = (chatId, isGroup) => {
    currentChatId = chatId;
    currentChatIsGroup = isGroup;
    lastMessageCount = 0;
    startMessageRefresh();

    if (isGroup) {
      setCurrentGroupId(chatId);
    } else {
      setCurrentGroupId(null);
    }
  };


  messageForm.addEventListener('submit', async e => {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (!message || isCurrentlyFetching) return;

    // Clear input immediately for better UX
    messageInput.value = '';

    try {
      const formData = new FormData(messageForm);
      formData.set('message-input', message);
      
      const res = await fetch('/send-message', { 
        method: 'POST', 
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      const data = await res.json();

      if (data.success) {
        await fetchAndRenderMessages(currentChatId, currentChatIsGroup, false);
      } else {
        messageInput.value = message;
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'alert alert-danger alert-dismissible fade show mt-2';
        errorMsg.innerHTML = `
          <small>Failed to send message. Please try again.</small>
          <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
        `;
        messageForm.appendChild(errorMsg);
        
        setTimeout(() => errorMsg.remove(), 3000);
      }
    } catch (err) {
      messageInput.value = message;
      
      const errorMsg = document.createElement('div');
      errorMsg.className = 'alert alert-warning alert-dismissible fade show mt-2';
      errorMsg.innerHTML = `
        <small>Network error. Please check your connection and try again.</small>
        <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
      `;
      messageForm.appendChild(errorMsg);
      setTimeout(() => errorMsg.remove(), 5000);
    }
  });
});
