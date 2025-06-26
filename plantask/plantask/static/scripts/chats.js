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
document.addEventListener('DOMContentLoaded', () => {
    const chatItems = document.querySelectorAll('.chat-item');

    chatItems.forEach(item => {
      item.addEventListener('click', () => {
        chatItems.forEach(chat => chat.classList.remove('active'));
        item.classList.add('active');
      });
    });
  });
document.addEventListener('DOMContentLoaded', () => {
    // Group image preview functionality
    const groupImageInput = document.getElementById('groupImageInput');
    const groupImagePreview = document.getElementById('groupImagePreview');
    const groupDescriptionTextarea = document.querySelector('textarea[name="group_description"]');
    const createGroupForm = document.querySelector('#createGroupModal form');

    // Handle image preview
    if (groupImageInput) {
        groupImageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validate file size (5MB max)
                if (file.size > 5 * 1024 * 1024) {
                    alert('File size must be less than 5MB');
                    this.value = '';
                    return;
                }

                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Please select a valid image file (JPG, PNG, JPEG)');
                    this.value = '';
                    return;
                }

                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    groupImagePreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                // Reset to default image
                groupImagePreview.src = '/static/default_pfp.svg';
            }
        });
    }

    // Character counter for description
    if (groupDescriptionTextarea) {
        // Create character counter element
        const charCounter = document.createElement('div');
        charCounter.className = 'char-counter';
        groupDescriptionTextarea.parentNode.appendChild(charCounter);

        function updateCharCounter() {
            const currentLength = groupDescriptionTextarea.value.length;
            const maxLength = 255;
            charCounter.textContent = `${currentLength}/${maxLength}`;
            
            // Update styling based on character count
            charCounter.classList.remove('warning', 'danger');
            if (currentLength > maxLength * 0.8) {
                charCounter.classList.add('warning');
            }
            if (currentLength > maxLength * 0.95) {
                charCounter.classList.add('danger');
            }
        }

        groupDescriptionTextarea.addEventListener('input', updateCharCounter);
        updateCharCounter(); // Initial count
    }

    // Form validation
    if (createGroupForm) {
        createGroupForm.addEventListener('submit', function(e) {
            const groupName = document.querySelector('input[name="group_name"]').value.trim();
            const selectedUsers = document.querySelectorAll('#groupSelectedUsers .list-group-item');

            // Validate group name
            if (!groupName) {
                e.preventDefault();
                alert('Please enter a group name');
                return;
            }

            // Validate at least one user is selected
            if (selectedUsers.length === 0) {
                e.preventDefault();
                alert('Please select at least one user for the group');
                return;
            }

            // Validate description length
            if (groupDescriptionTextarea && groupDescriptionTextarea.value.length > 255) {
                e.preventDefault();
                alert('Group description must be 255 characters or less');
                return;
            }
        });
    }

    // Reset form when modal is closed
    const createGroupModal = document.getElementById('createGroupModal');
    if (createGroupModal) {
        createGroupModal.addEventListener('hidden.bs.modal', function() {
            // Reset form
            createGroupForm.reset();
            
            // Reset image preview
            if (groupImagePreview) {
                groupImagePreview.src = '/static/default_pfp.svg';
            }
            
            // Reset character counter
            if (groupDescriptionTextarea) {
                const charCounter = document.querySelector('.char-counter');
                if (charCounter) {
                    charCounter.textContent = '0/255';
                    charCounter.classList.remove('warning', 'danger');
                }
            }
            
            // Clear selected users
            const selectedUsers = document.getElementById('groupSelectedUsers');
            const hiddenInputs = document.getElementById('groupHiddenInputs');
            if (selectedUsers) selectedUsers.innerHTML = '';
            if (hiddenInputs) hiddenInputs.innerHTML = '';
            
            // Disable submit button
            const submitBtn = document.getElementById('createGroupSubmit');
            if (submitBtn) submitBtn.disabled = true;
        });
    }
});
document.addEventListener('DOMContentLoaded', function() {
    let currentGroupId = null;

    // Group image modal functionality
    const groupAvatarImg = document.getElementById('group-avatar-img');
    const groupImageModal = new bootstrap.Modal(document.getElementById('groupImageModal'));
    const groupImageForm = document.getElementById('group-image-form');
    const groupImageInput = document.getElementById('group-image-input');
    const groupImagePreview = document.getElementById('group-image-preview');
    const groupImagePreviewContainer = document.getElementById('group-image-preview-container');
    const groupImageSubmit = document.getElementById('group-image-submit');
    const currentGroupImage = document.getElementById('current-group-image');
    const groupEntityIdInput = document.getElementById('group-entity-id');

    // Open group image modal
    groupAvatarImg.addEventListener('click', function() {
        if (currentGroupId) {
            // Set current image in modal
            currentGroupImage.src = this.src;
            // Set the entity ID for the form
            groupEntityIdInput.value = currentGroupId;
            groupImageModal.show();
        }
    });

    // Handle image file selection
    groupImageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
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

    // The form will now submit normally to the file_upload_page route
    // Remove the fetch-based form submission handler

    // Group name editing
    const editGroupNameBtn = document.getElementById('edit-group-name-btn');
    const groupNameDisplay = document.getElementById('group-name-display');
    const groupNameForm = document.getElementById('group-name-form');
    const groupNameInput = document.getElementById('group-name-input');
    const cancelNameEdit = document.getElementById('cancel-name-edit');

    editGroupNameBtn.addEventListener('click', function() {
        groupNameInput.value = groupNameDisplay.textContent;
        groupNameDisplay.classList.add('d-none');
        this.classList.add('d-none');
        groupNameForm.classList.remove('d-none');
        groupNameInput.focus();
    });

    cancelNameEdit.addEventListener('click', function() {
        groupNameForm.classList.add('d-none');
        groupNameDisplay.classList.remove('d-none');
        editGroupNameBtn.classList.remove('d-none');
    });

    groupNameForm.addEventListener('submit', function(e) {
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
                
                // Update the chat name in the chat info header
                const chatInfoHeader = document.querySelector('.ChatInfo h4');
                if (chatInfoHeader) {
                    chatInfoHeader.textContent = groupNameInput.value;
                }
            } else {
                showNotification(data.error || 'Error updating group name', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error updating group name', 'error');
        });
    });

    // Group description editing
    const editGroupDescriptionBtn = document.getElementById('edit-group-description-btn');
    const groupDescriptionDisplay = document.getElementById('group-description-display');
    const groupDescriptionForm = document.getElementById('group-description-form');
    const groupDescriptionInput = document.getElementById('group-description-input');
    const cancelDescriptionEdit = document.getElementById('cancel-description-edit');

    editGroupDescriptionBtn.addEventListener('click', function() {
        groupDescriptionInput.value = groupDescriptionDisplay.textContent === 'Group Description' ? '' : groupDescriptionDisplay.textContent;
        groupDescriptionDisplay.classList.add('d-none');
        this.classList.add('d-none');
        groupDescriptionForm.classList.remove('d-none');
        groupDescriptionInput.focus();
    });

    cancelDescriptionEdit.addEventListener('click', function() {
        groupDescriptionForm.classList.add('d-none');
        groupDescriptionDisplay.classList.remove('d-none');
        editGroupDescriptionBtn.classList.remove('d-none');
    });

    groupDescriptionForm.addEventListener('submit', function(e) {
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
            console.error('Error:', error);
            showNotification('Error updating group description', 'error');
        });
    });

    // Function to set the current group ID when a group chat is selected
    window.setCurrentGroupId = function(groupId) {
        currentGroupId = groupId;
    };

    // Utility function to show notifications
    function showNotification(message, type) {
        // You can implement this based on your existing notification system
        console.log(`${type}: ${message}`);
    }
});