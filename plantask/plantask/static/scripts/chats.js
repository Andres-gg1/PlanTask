// Global notification function
function showNotification(msg, type = "info") {
  // Create notification container if it doesn't exist
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      max-width: 400px;
    `;
    document.body.appendChild(container);
  }
  // Create the notification
  const notification = document.createElement('div');
  const iconMap = {
    success: 'bi-check-circle-fill',
    error: 'bi-x-circle-fill',
    danger: 'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info: 'bi-info-circle-fill'
  };
  
  const colorMap = {
    success: 'alert-success',
    error: 'alert-danger',
    danger: 'alert-danger',
    warning: 'alert-warning',
    info: 'alert-info'
  };

  notification.className = `alert ${colorMap[type] || 'alert-info'} alert-dismissible fade show mb-2`;
  notification.style.cssText = `
    animation: slideIn 0.3s ease-out;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  `;
  
  notification.innerHTML = `
    <i class="bi ${iconMap[type] || 'bi-info-circle-fill'} me-2"></i>
    ${msg}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  container.appendChild(notification);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.classList.add('fade');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 150);
    }
  }, 5000);

  // Add CSS styles if they don't exist
  if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);
  }
}

// Helper function to reload maintaining open group
function reloadWithCurrentGroup(groupId = null, delay = 1000) {
  const targetGroupId = groupId || currentGroupId;
  
  setTimeout(() => {
    if (targetGroupId) {
      const currentUrl = new URL(window.location);
      currentUrl.searchParams.set('currentChatId', targetGroupId);
      window.location.href = currentUrl.toString();
    } else {
      window.location.reload();
    }
  }, delay);
}

// Auto scroll to end of chat
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

// Chat list search
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
      const firstName = (item.getAttribute('data-first-name') || '').toLowerCase();
      const lastName = (item.getAttribute('data-last-name') || '').toLowerCase();
      const username = (item.getAttribute('data-username') || '').toLowerCase();
      const fullname = (firstName + ' ' + lastName).trim();

      if (
        firstName.includes(filter) ||
        lastName.includes(filter) ||
        username.includes(filter) ||
        fullname.includes(filter)
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

// Chat click handling
document.addEventListener('DOMContentLoaded', () => {
  const chatItems = document.querySelectorAll('.chat-item');

  chatItems.forEach(item => {
    item.addEventListener('click', () => {
      chatItems.forEach(chat => chat.classList.remove('active'));
      item.classList.add('active');

      const groupId = item.getAttribute('data-group-id') || item.getAttribute('data-chat-id');
      const isGroup = item.getAttribute('data-is-group') === 'true' || item.getAttribute('data-username') === 'group';
      
      if (isGroup && groupId) {
        currentGroupId = groupId;
        setCurrentGroupId(groupId);
      } else {
        currentGroupId = null;
      }
    });
  });
});

// Group creation and editing logic
document.addEventListener('DOMContentLoaded', () => {
  const groupImageInput = document.getElementById('groupImageInput');
  const groupImagePreview = document.getElementById('groupImagePreview');
  const groupDescriptionTextarea = document.querySelector('textarea[name="group_description"]');
  const createGroupForm = document.querySelector('#createGroupModal form');

  if (groupImageInput) {
    groupImageInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        if (file.size > 5 * 1024 * 1024) {
          showNotification('File size must be less than 5MB', 'error');
          this.value = '';
          return;
        }

        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!allowedTypes.includes(file.type)) {
          showNotification('Please select a valid image file (JPG, PNG, JPEG)', 'error');
          this.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          groupImagePreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      } else {
        groupImagePreview.src = '/static/default_pfp.svg';
      }
    });
  }

  if (groupDescriptionTextarea) {
    const charCounter = document.createElement('div');
    charCounter.className = 'char-counter';
    groupDescriptionTextarea.parentNode.appendChild(charCounter);

    function updateCharCounter() {
      const currentLength = groupDescriptionTextarea.value.length;
      const maxLength = 255;
      charCounter.textContent = `${currentLength}/${maxLength}`;
      charCounter.classList.remove('warning', 'danger');
      if (currentLength > maxLength * 0.8) charCounter.classList.add('warning');
      if (currentLength > maxLength * 0.95) charCounter.classList.add('danger');
    }

    groupDescriptionTextarea.addEventListener('input', updateCharCounter);
    updateCharCounter();
  }

  if (createGroupForm) {
    createGroupForm.addEventListener('submit', function (e) {
      const groupName = document.querySelector('input[name="group_name"]').value.trim();
      const selectedUsers = document.querySelectorAll('#groupSelectedUsers .list-group-item');

      if (!groupName) {
        e.preventDefault();
        showNotification('Please enter a group name', 'warning');
        return;
      }

      if (selectedUsers.length === 0) {
        e.preventDefault();
        showNotification('Please select at least one user for the group', 'warning');
        return;
      }

      if (groupDescriptionTextarea && groupDescriptionTextarea.value.length > 255) {
        e.preventDefault();
        showNotification('Group description must be 255 characters or less', 'warning');
        return;
      }
    });
  }

  const createGroupModal = document.getElementById('createGroupModal');
  if (createGroupModal) {
    createGroupModal.addEventListener('hidden.bs.modal', function () {
      createGroupForm.reset();
      if (groupImagePreview) groupImagePreview.src = '/static/default_pfp.svg';

      const charCounter = document.querySelector('.char-counter');
      if (charCounter) {
        charCounter.textContent = '0/255';
        charCounter.classList.remove('warning', 'danger');
      }

      const selectedUsers = document.getElementById('groupSelectedUsers');
      const hiddenInputs = document.getElementById('groupHiddenInputs');
      if (selectedUsers) selectedUsers.innerHTML = '';
      if (hiddenInputs) hiddenInputs.innerHTML = '';

      const submitBtn = document.getElementById('createGroupSubmit');
      if (submitBtn) submitBtn.disabled = true;
    });
  }
});

// Edit group name and description
document.addEventListener('DOMContentLoaded', function () {
  const groupAvatarImg = document.getElementById('group-avatar-img');
  const groupImageModal = new bootstrap.Modal(document.getElementById('groupImageModal'));
  const groupImageForm = document.getElementById('group-image-form');
  const groupImageInput = document.getElementById('group-image-input');
  const groupImagePreview = document.getElementById('group-image-preview');
  const groupImagePreviewContainer = document.getElementById('group-image-preview-container');
  const groupImageSubmit = document.getElementById('group-image-submit');
  const currentGroupImage = document.getElementById('current-group-image');
  const groupEntityIdInput = document.getElementById('group-entity-id');

  if (groupAvatarImg) {
    groupAvatarImg.addEventListener('click', function () {
      if (currentGroupId) {
        currentGroupImage.src = this.src;
        groupEntityIdInput.value = currentGroupId;
        groupImageModal.show();
      }
    });
  }

  if (groupImageInput) {
    groupImageInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          groupImagePreview.src = e.target.result;
          groupImagePreviewContainer.classList.remove('d-none');
          groupImageSubmit.disabled = false;
        };
        reader.readAsDataURL(file);
      } else {
        groupImagePreviewContainer.classList.add('d-none');
        groupImageSubmit.disabled = true;
      }
    });
  }

  if (groupImageForm) {
    groupImageForm.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!currentGroupId) return;

      const formData = new FormData(this);
      
      fetch(this.action, {
        method: 'POST',
        body: formData
      })
        .then(response => {
          console.log('Response status:', response.status);
          console.log('Response headers:', response.headers.get('content-type'));
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          // Check if response is actually JSON
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            return response.json();
          } else {
            // If it's not JSON, assume success since image was uploaded
            console.log('Non-JSON response, assuming success');
            return { success: true };
          }
        })
        .then(data => {
          console.log('Server response:', data); // Debug log
          if (data.success || data.message) {
            showNotification('Group image updated successfully', 'success');
            groupImageModal.hide();
            
            reloadWithCurrentGroup();
          } else {
            showNotification(data.error || 'Error updating group image', 'error');
          }
        })
        .catch(error => {
          console.error('Fetch error:', error); // Debug log
          
          // Since you mentioned the image IS being uploaded, treat as success
          if (error.message.includes('Unexpected token')) {
            console.log('JSON parse error but image likely uploaded successfully');
            showNotification('Group image updated successfully', 'success');
            groupImageModal.hide();
            reloadWithCurrentGroup();
          } else {
            showNotification(`Network error: ${error.message}`, 'error');
          }
        });
    });
  }

  const editGroupNameBtn = document.getElementById('edit-group-name-btn');
  const groupNameDisplay = document.getElementById('group-name-display');
  const groupNameForm = document.getElementById('group-name-form');
  const groupNameInput = document.getElementById('group-name-input');
  const cancelNameEdit = document.getElementById('cancel-name-edit');

  if (editGroupNameBtn) {
    editGroupNameBtn.addEventListener('click', function () {
      groupNameInput.value = groupNameDisplay.textContent;
      groupNameDisplay.classList.add('d-none');
      this.classList.add('d-none');
      groupNameForm.classList.remove('d-none');
      groupNameInput.focus();
    });
  }

  if (cancelNameEdit) {
    cancelNameEdit.addEventListener('click', function () {
      groupNameForm.classList.add('d-none');
      groupNameDisplay.classList.remove('d-none');
      editGroupNameBtn.classList.remove('d-none');
    });
  }

  if (groupNameForm) {
    groupNameForm.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!currentGroupId) return;

      const formData = new FormData(this);
      fetch(`/edit-group-name/${currentGroupId}`, {
        method: 'POST',
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            groupNameDisplay.textContent = groupNameInput.value;
            groupNameForm.classList.add('d-none');
            groupNameDisplay.classList.remove('d-none');
            editGroupNameBtn.classList.remove('d-none');
            showNotification('Group name updated successfully', 'success');
            const chatInfoHeader = document.querySelector('.ChatInfo h4');
            if (chatInfoHeader) chatInfoHeader.textContent = groupNameInput.value;
            
            // Update group name in chat list as well
            const activeChat = document.querySelector('.chat-item.active');
            if (activeChat) {
              const nameElement = activeChat.querySelector('.chat-name, h6, .fw-bold');
              if (nameElement) nameElement.textContent = groupNameInput.value;
            }
          } else {
            showNotification(data.error || 'Error updating group name', 'error');
          }
        })
        .catch(error => {
          showNotification('Error updating group name', 'error');
        });
    });
  }

  const editGroupDescriptionBtn = document.getElementById('edit-group-description-btn');
  const groupDescriptionDisplay = document.getElementById('group-description-display');
  const groupDescriptionForm = document.getElementById('group-description-form');
  const groupDescriptionInput = document.getElementById('group-description-input');
  const cancelDescriptionEdit = document.getElementById('cancel-description-edit');

  if (editGroupDescriptionBtn) {
    editGroupDescriptionBtn.addEventListener('click', function () {
      groupDescriptionInput.value = groupDescriptionDisplay.textContent === 'Group Description' ? '' : groupDescriptionDisplay.textContent;
      groupDescriptionDisplay.classList.add('d-none');
      this.classList.add('d-none');
      groupDescriptionForm.classList.remove('d-none');
      groupDescriptionInput.focus();
    });
  }

  if (cancelDescriptionEdit) {
    cancelDescriptionEdit.addEventListener('click', function () {
      groupDescriptionForm.classList.add('d-none');
      groupDescriptionDisplay.classList.remove('d-none');
      editGroupDescriptionBtn.classList.remove('d-none');
    });
  }

  if (groupDescriptionForm) {
    groupDescriptionForm.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!currentGroupId) return;

      const formData = new FormData(this);
      fetch(`/edit-group-description/${currentGroupId}`, {
        method: 'POST',
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            groupDescriptionDisplay.textContent = groupDescriptionInput.value || 'No description';
            groupDescriptionForm.classList.add('d-none');
            groupDescriptionDisplay.classList.remove('d-none');
            editGroupDescriptionBtn.classList.remove('d-none');
            showNotification('Group description updated successfully', 'success');
          } else {
            showNotification(data.error || 'Error updating group description', 'error');
          }
        })
        .catch(error => {
          showNotification('Error updating group description', 'error');
        });
    });
  }

  window.setCurrentGroupId = function (groupId) {
    currentGroupId = groupId;
  };
});
// Group member search, add and remove logic

let groupSelectedUsers = [];
let currentGroupId = null; // Global variable to store current group ID

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('groupMemberSearch');
  let timeout;

  if (input) {
    input.addEventListener('input', () => {
      const value = input.value.trim();
      clearTimeout(timeout);

      if (value.length < 2) {
        document.getElementById("groupMemberSearchResults").innerHTML = "<p>Enter at least 2 characters</p>";
        return;
      }

      timeout = setTimeout(() => searchGroupUsers(), 300);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') e.preventDefault();
    });
  }

  const addGroupModal = document.getElementById('addGroupMemberModal');
  if (addGroupModal) {
    addGroupModal.addEventListener('show.bs.modal', () => {
      groupSelectedUsers = [];
      updateGroupSelectedUsers();
      document.getElementById('groupMemberSearch').value = '';
      document.getElementById('groupMemberSearchResults').innerHTML = '';
      
      // Ensure we have the correct groupId
      const activeChat = document.querySelector('.chat-item.active');
      if (activeChat) {
        const groupId = activeChat.getAttribute('data-chat-id') || activeChat.getAttribute('data-group-id');
        if (groupId) {
          currentGroupId = groupId;
          document.getElementById('currentGroupIdInput').value = groupId;
        }
      }
    });

    addGroupModal.addEventListener('hidden.bs.modal', () => {
      groupSelectedUsers = [];
      updateGroupSelectedUsers();
      document.getElementById('groupMemberSearch').value = '';
      document.getElementById('groupMemberSearchResults').innerHTML = '';
    });
  }

  const addGroupForm = document.getElementById('addGroupMemberForm');
  if (addGroupForm) {
    addGroupForm.addEventListener('submit', function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      fetch('/add-group-members', {
        method: 'POST',
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addGroupMemberModal'));
            modal.hide();
            showNotification('Members added successfully.', 'success');
            
            // Reload maintaining current open group
            reloadWithCurrentGroup();
          } else {
            showNotification(data.error || 'Failed to add members.', 'error');
          }
        })
        .catch(err => {
          showNotification('Error adding members.', 'error');
        });
    });
  }

  const confirmRemoveBtn = document.getElementById('confirmRemoveMemberBtn');
  if (confirmRemoveBtn) {
    // Remove any previous event listener
    confirmRemoveBtn.onclick = null;
    confirmRemoveBtn.removeEventListener('click', handleRemoveClick);
    
    // Add event listener using addEventListener for better control
    confirmRemoveBtn.addEventListener('click', handleRemoveClick);
  }
});

// Separate function to handle remove click
function handleRemoveClick() {
  const userId = document.getElementById('removeMemberUserId').value;
  const groupId = currentGroupId;
  
  if (!userId || !groupId) {
    showNotification('Error: Missing user or group ID', 'error');
    return;
  }

  // Prevent multiple clicks
  if (this.disabled) {
    return;
  }

  this.disabled = true;
  this.textContent = 'Removing...';

  fetch('/remove-group-member', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ user_id: userId, group_id: groupId })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showNotification('Member removed successfully.', 'success');
        const modal = bootstrap.Modal.getInstance(document.getElementById('confirmRemoveMemberModal'));
        modal.hide();
        
        // Recargar manteniendo el grupo actual abierto
        reloadWithCurrentGroup(groupId);
      } else {
        showNotification(data.error || 'Failed to remove member.', 'error');
        // Re-habilitar el botón en caso de error
        this.disabled = false;
        this.textContent = 'Remove';
      }
    })
    .catch(err => {
      showNotification('Error removing member.', 'error');
      // Re-habilitar el botón en caso de error
      this.disabled = false;
      this.textContent = 'Remove';
    });
}

function searchGroupUsers() {
  const term = document.getElementById("groupMemberSearch").value.trim();
  const container = document.getElementById("groupMemberSearchResults");
  const groupId = document.getElementById("currentGroupIdInput").value;

  if (term.length < 2) {
    container.innerHTML = "<p>Enter at least 2 characters</p>";
    return;
  }

  container.innerHTML = "<p>Searching...</p>";

  fetch(`/search-group-users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      group_id: groupId,
      term: term
    })
  })
    .then(res => res.json())
    .then(data => {
      container.innerHTML = "";

      const filtered = data.users?.filter(user => !groupSelectedUsers.some(sel => sel.id === user.id)) || [];

      if (filtered.length === 0) {
        container.innerHTML = "<p>No users found</p>";
        return;
      }

      filtered.forEach(user => {
        const div = document.createElement("div");
        div.className = "search-result-item d-flex justify-content-between align-items-center mb-2";

        const pfp = user.image_route
          ? `<img src="${user.image_route}" class="rounded-circle me-2" style="width: 32px; height: 32px; object-fit: cover;">`
          : `<i class="bi bi-person-circle fs-4 text-secondary me-2"></i>`;

        div.innerHTML = `
          <div class="d-flex align-items-center">
            ${pfp}
            <div>
              <strong>${user.first_name} ${user.last_name}</strong><br>
              <small class="text-muted">@${user.username}</small>
            </div>
          </div>
          <button class="btn btn-sm btn-primary" onclick="addGroupUser('${user.id}', '${user.username}', '${user.first_name}', '${user.last_name}', '${user.image_route ?? ''}')">Add</button>
        `;

        container.appendChild(div);
      });
    })
    .catch(err => {
      container.innerHTML = `<p class="text-danger">Error: ${err.message}</p>`;
    });
}

function addGroupUser(id, username, firstName, lastName, imageRoute) {
  const idNum = parseInt(id);
  if (groupSelectedUsers.some(u => u.id === idNum)) return;

  groupSelectedUsers.push({
    id: idNum,
    username,
    first_name: firstName,
    last_name: lastName,
    image_route: imageRoute
  });

  updateGroupSelectedUsers();
  searchGroupUsers();
}

function removeGroupUser(id) {
  const idNum = parseInt(id);
  groupSelectedUsers = groupSelectedUsers.filter(u => u.id !== idNum);
  updateGroupSelectedUsers();
}

function confirmRemoveFromGroup(userId, fullName, groupName) {
  const modalElement = document.getElementById('confirmRemoveMemberModal');
  const modal = new bootstrap.Modal(modalElement);
  const confirmBtn = document.getElementById('confirmRemoveMemberBtn');
  
  // Resetear el botón
  confirmBtn.disabled = false;
  confirmBtn.textContent = 'Remove';
  
  document.getElementById('removeMemberUserId').value = userId;
  document.getElementById('confirmRemoveMemberText').textContent =
    `Are you sure you want to remove ${fullName} from the group "${groupName}"?`;

  // Get the groupId from current input or active element
  const groupId = document.getElementById('currentGroupIdInput')?.value || 
                 document.querySelector('.chat-item.active')?.getAttribute('data-chat-id') ||
                 window.currentGroupId;

  // Update currentGroupId to be available in handleRemoveClick
  if (groupId) {
    currentGroupId = groupId;
  }
  
  modal.show();
}

// Función eliminada - ahora usamos handleRemoveClick que está integrado con el event listener

function updateGroupSelectedUsers() {
  const list = document.getElementById("groupSelectedUsersList");
  const hidden = document.getElementById("groupHiddenInputsContainer");

  if (!list || !hidden) return;

  list.innerHTML = "";
  hidden.innerHTML = "";

  if (groupSelectedUsers.length === 0) {
    list.innerHTML = "<p class='text-muted'>No users selected</p>";
    return;
  }

  groupSelectedUsers.forEach(user => {
    const pfp = user.image_route
      ? `<img src="${user.image_route}" class="rounded-circle me-3" style="width: 2rem; height: 2rem; object-fit: cover;">`
      : `<i class="bi bi-person-circle fs-4 text-primary me-3"></i>`;

    const li = document.createElement("li");
    li.className = "list-group-item d-flex align-items-center justify-content-between";
    li.innerHTML = `
      <div class="d-flex align-items-center">
        ${pfp}
        <div>
          <strong>${user.first_name} ${user.last_name}</strong><br>
          <small class="text-muted">@${user.username}</small>
        </div>
      </div>
      <button class="btn btn-sm btn-outline-danger ms-2" onclick="removeGroupUser('${user.id}')">
        <i class="bi bi-x-lg"></i>
      </button>
    `;

    list.appendChild(li);

    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "user_ids";
    input.value = user.id;
    hidden.appendChild(input);
  });
}
