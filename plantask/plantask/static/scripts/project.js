let selectedUsers = [];

document.addEventListener('DOMContentLoaded', function () {
    // Debounce search input
    const input = document.getElementById('usernameSearch');
    let searchTimeout;

    if (input) {
        input.addEventListener('input', function () {
            const value = input.value.trim();
            clearTimeout(searchTimeout);

            if (value.length < 2) {
                document.getElementById("userSearchResults").innerHTML = "<p>Please enter at least 2 characters</p>";
                return;
            }

            searchTimeout = setTimeout(() => {
                searchUsers();
            }, 300);
        });
    }

    // Optional: reset selectedUsers when modal opens
    const addMemberModal = document.getElementById('addMemberModal');
    if (addMemberModal) {
        addMemberModal.addEventListener('show.bs.modal', () => {
            selectedUsers = [];
            updateSelectedUsers();
            document.getElementById('usernameSearch').value = '';
            document.getElementById('userSearchResults').innerHTML = '';
        });
    }
});
function searchUsers() {
    const searchTerm = document.getElementById("usernameSearch").value.trim();
    const resultsContainer = document.getElementById("userSearchResults");

    if (searchTerm.length < 2) {
        resultsContainer.innerHTML = "<p>Please enter at least 2 characters</p>";
        return;
    }

    resultsContainer.innerHTML = "<p>Searching users...</p>";
    const projectId = document.getElementById("projectId").value;

    fetch(`/search-users?q=${encodeURIComponent(searchTerm)}&project_id=${projectId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Search error: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            resultsContainer.innerHTML = "";

            const filteredData = data.filter(user => !selectedUsers.some(sel => sel.id === user.id));

            if (filteredData.length === 0) {
                resultsContainer.innerHTML = "<p>No users found</p>";
                return;
            }

            filteredData.forEach(user => {
                const userItem = document.createElement("div");
                userItem.classList.add("search-result-item", "d-flex", "justify-content-between", "align-items-center", "mb-2");

                const pfp = user.image_route
                    ? `<img src="${user.image_route}" alt="PFP" class="rounded-circle me-2" style="width: 32px; height: 32px; object-fit: cover;">`
                    : `<i class="bi bi-person-circle fs-4 text-secondary me-2"></i>`;

                userItem.innerHTML = `
                    <div class="d-flex align-items-center">
                        ${pfp}
                        <div>
                            <strong>${user.first_name} ${user.last_name}</strong><br>
                            <small class="text-muted">@${user.username}</small>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-primary" onclick="addUser('${user.id}', '${user.username}', '${user.first_name}', '${user.last_name}', '${user.image_route ?? ''}')">Add</button>
                `;

                resultsContainer.appendChild(userItem);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            resultsContainer.innerHTML =
                `<p class="text-danger">Error searching users: ${error.message}</p>`;
        });
}

function addUser(userId, username, firstName, lastName, imageRoute) {
    const idNum = parseInt(userId);
    if (selectedUsers.some(u => u.id === idNum)) {
        return;
    }
    selectedUsers.push({ id: idNum, username, first_name: firstName, last_name: lastName });
    updateSelectedUsers();
    searchUsers(); 
}

function removeUser(userId) {
    selectedUsers = selectedUsers.filter(user => user.id !== userId);
    updateSelectedUsers();
}

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

        // Hidden input for form submission
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "user_ids"; // backend should accept this as a list
        hiddenInput.value = user.id;
        hiddenInputsContainer.appendChild(hiddenInput);
    });
}
