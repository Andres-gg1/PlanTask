document.addEventListener('DOMContentLoaded', function () {
  const notificationsModalElement = document.getElementById('notificationsModal');
  const notificationsModal = new bootstrap.Modal(notificationsModalElement);

  notificationsModalElement.addEventListener('hidden.bs.modal', function () {
    document.body.classList.remove('modal-open');
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
      backdrop.remove();
    }
  });

  const notificationsBtn = document.querySelector('.navbar-icon[title="Notifications"]');
  const notificationsList = document.getElementById('notificationsList');

  notificationsBtn?.addEventListener('click', async function (e) {
    e.preventDefault();

    const url = notificationsBtn.dataset.url;

    notificationsList.innerHTML = '<div class="notification"><div class="notification-body">Loading...</div></div>';

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }

      const data = await response.json();

      notificationsList.innerHTML = '';
      if (data.notifications.length > 0) {
        data.notifications.forEach(notification => {
          const notificationCard = document.createElement('div');
          notificationCard.className = 'notification mb-3';

          const notificationBody = document.createElement('div');
          notificationBody.className = 'notification-body';

          const notificationTitle = document.createElement('h5');
          notificationTitle.className = 'notification-text';
          notificationTitle.textContent = notification.message;

          const notificationDate = document.createElement('p');
          notificationDate.className = 'notification-text received-on';
          notificationDate.textContent = `Received on: ${notification.created_at}`;

          notificationBody.appendChild(notificationTitle);
          notificationBody.appendChild(notificationDate);
          notificationCard.appendChild(notificationBody);

          notificationsList.appendChild(notificationCard);
        });
      } else {
        notificationsList.innerHTML = '<div class="notification"><div class="notification-body">No notifications available</div></div>';
      }

      notificationsModal.show();

    } catch (error) {
      notificationsList.innerHTML = '<div class="notification"><div class="notification-body text-danger">Error loading notifications</div></div>';
      console.error(error);
    }
  });
});