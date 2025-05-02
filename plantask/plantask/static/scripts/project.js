const dropdownButton = document.getElementById('membersDropdown');
const dropdownIcon = document.getElementById('dropdownIcon');

dropdownButton.addEventListener('click', function () {
    const isOpen = dropdownButton.getAttribute('aria-expanded') === 'true';
    if (isOpen) {
        dropdownIcon.classList.remove('bi-chevron-down');
        dropdownIcon.classList.add('bi-chevron-up');  // Cambiar a chevron hacia arriba cuando esté abierto
    } else {
        dropdownIcon.classList.remove('bi-chevron-up');
        dropdownIcon.classList.add('bi-chevron-down');  // Cambiar a chevron hacia abajo cuando esté cerrado
    }
});

let selectedUsers = [];

document.addEventListener('DOMContentLoaded', function() {
    const searchField = document.getElementById("usernameSearch");
    if (searchField) {
        searchField.addEventListener("keyup", function(event) {
            if (event.key === "Enter") {
                searchUsers();
            }
        });
    }
    
    // Initialize the selected users list
    updateSelectedUsers();
    
    // Add form submission event listener for debugging
    const addMemberForm = document.getElementById("addMemberForm");
    if (addMemberForm) {
        addMemberForm.addEventListener("submit", function(event) {
            console.log("Form submitting with selected users:", selectedUsers);
            
            // Check if there are any selected users
            if (selectedUsers.length === 0) {
                console.log("No users selected, preventing form submission");
                event.preventDefault();
                alert("Please select at least one user to add.");
                return false;
            }
            
            // Ensure hidden inputs are populated correctly
            const hiddenInputsContainer = document.getElementById("hiddenInputsContainer");
            if (hiddenInputsContainer.children.length === 0) {
                console.log("No hidden inputs found, regenerating them");
                selectedUsers.forEach(user => {
                    const hiddenInput = document.createElement("input");
                    hiddenInput.type = "hidden";
                    hiddenInput.name = "user_ids";
                    hiddenInput.value = user.id;
                    hiddenInputsContainer.appendChild(hiddenInput);
                });
            }
            
            return true;
        });
    }
});

// Function to search for users
function searchUsers() {
    const searchTerm = document.getElementById("usernameSearch").value;
    
    if (searchTerm.trim() === '' || searchTerm.trim().length < 2) {
        document.getElementById("userSearchResults").innerHTML = "<p>Please enter at least 2 characters</p>";
        return;
    }
    
    // Show loading indicator
    document.getElementById("userSearchResults").innerHTML = "<p>Searching users...</p>";
    
    // Get the project ID from the current URL
    const urlPath = window.location.pathname;
    const projectIdMatch = urlPath.match(/\/project\/(\d+)/);
    const projectId = projectIdMatch ? projectIdMatch[1] : null;
    
    // Use the correct search URL path
    const searchUrl = `/search-users?username=${encodeURIComponent(searchTerm)}${projectId ? '&project_id=' + projectId : ''}`;
    
    console.log("Searching with URL:", searchUrl);
    
    // Perform search request
    fetch(searchUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Search error: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("Search results:", data);
            
            const resultsContainer = document.getElementById("userSearchResults");
            resultsContainer.innerHTML = ""; // Clear previous results

            if (data.length === 0) {
                resultsContainer.innerHTML = "<p>No users found</p>";
                return;
            }

            data.forEach(user => {
                const userItem = document.createElement("div");
                userItem.classList.add("search-result-item", "d-flex", "justify-content-between", "align-items-center");
                userItem.innerHTML = `
                    <span>@${user.username}</span>
                    <button type="button" class="btn btn-sm btn-primary" onclick="addUser('${user.id}', '${user.username}', '${user.first_name}', '${user.last_name}')">Add</button>
                `;
                resultsContainer.appendChild(userItem);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById("userSearchResults").innerHTML = 
                `<p class="text-danger">Error searching users: ${error.message}</p>`;
        });
}

function addUser(userId, username, firstName, lastName) {
    console.log(`Adding user: ${username} (ID: ${userId})`);
    
    if (!selectedUsers.some(user => user.id === userId)) {
        // Usar los valores de firstName y lastName obtenidos
        selectedUsers.push({ id: userId, username: username, first_name: firstName, last_name: lastName });
        updateSelectedUsers();
        document.getElementById("usernameSearch").value = "";
        document.getElementById("userSearchResults").innerHTML = "";
    } else {
        console.log(`User ${username} is already selected`);
    }
}

// Function to remove a user from the selected list
function removeUser(userId) {
    console.log(`Removing user with ID: ${userId}`);
    
    // Filter out the user with the specified ID
    selectedUsers = selectedUsers.filter(user => user.id !== userId);
    
    // Update the UI to reflect the changes
    updateSelectedUsers();
}

// Function to update the UI to show selected users
function updateSelectedUsers() {
    const selectedUsersList = document.getElementById("selectedUsersList");
    const hiddenInputsContainer = document.getElementById("hiddenInputsContainer");
    
    selectedUsersList.innerHTML = "";
    hiddenInputsContainer.innerHTML = "";

    if (selectedUsers.length === 0) {
        selectedUsersList.innerHTML = "<p class='text-muted'>No users selected</p>";
        return;
    }

    selectedUsers.forEach(user => {
        const li = document.createElement("li");
        li.className = "list-group-item d-flex align-items-center justify-content-between";
        li.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi-person-circle fs-4 text-primary me-3"></i>
                <div>
                    <strong>${user.first_name} ${user.last_name}</strong><br>
                    <small class="text-muted">@${user.username}</small>
                </div>
            </div>
            <button class="btn btn-sm btn-outline-danger ms-2" onclick="removeUser('${user.id}')">
                <i class="bi-x-lg"></i>
            </button>
        `;
        selectedUsersList.appendChild(li);

        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "user_ids";
        hiddenInput.value = user.id;
        hiddenInputsContainer.appendChild(hiddenInput);
    });
}

document.addEventListener('DOMContentLoaded', function () {
    let selectedFormToSubmit = null;

    document.querySelectorAll('.remove-member-form').forEach(form => {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            selectedFormToSubmit = form;

            const memberName = form.getAttribute('data-member-name');
            document.getElementById('removeMemberMessage').textContent =
                `Are you sure you want to remove ${memberName}?`;

            const modal = new bootstrap.Modal(document.getElementById('confirmRemoveMemberModal'));
            modal.show();
        });
    });

    document.getElementById('confirmRemoveBtn').addEventListener('click', function () {
        if (selectedFormToSubmit) {
            selectedFormToSubmit.submit();
        }
    });
});
  