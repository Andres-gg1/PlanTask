document.addEventListener('DOMContentLoaded', function () {
    // Handle edit member button clicks
    document.querySelectorAll('.edit-member-btn').forEach(button => {
        button.addEventListener('click', function () {
            const userId = parseInt(this.dataset.userId);
            document.getElementById('editMemberUserId').value = userId;

            const firstName = this.dataset.firstName;
            const lastName = this.dataset.lastName;
            const modalTitle = document.getElementById('editMemberModalLabel');
            modalTitle.textContent = `Edit Member | ${firstName} ${lastName}`;

            const userLabelIds = window.memberLabels[userId] || [];

            document.querySelectorAll('.toggle-label-btn').forEach(btn => {
                const labelId = parseInt(btn.dataset.labelId);
                const checkbox = btn.parentElement.querySelector('.label-checkbox');
                const isAssigned = userLabelIds.includes(labelId);

                checkbox.checked = isAssigned;
                if (isAssigned) {
                    btn.classList.add('assigned');
                    btn.style.backgroundColor = '#28a745';
                    btn.style.color = '#fff';
                    btn.innerHTML = '<i class="bi bi-check-lg"></i>';
                } else {
                    btn.classList.remove('assigned');
                    btn.style.backgroundColor = '#FAFAFA';
                    btn.style.color = '';
                    btn.innerHTML = '';
                }
            });
        });
    });

    // Handle label toggle clicks
    document.querySelectorAll('.toggle-label-btn').forEach(button => {
        button.addEventListener('click', function () {
            const checkbox = this.parentElement.querySelector('.label-checkbox');
            const isCurrentlyAssigned = this.classList.contains('assigned');
            checkbox.checked = !isCurrentlyAssigned;
        });
    });
});
