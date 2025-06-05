
document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('navbarToggle');
  const navbarContent = document.getElementById('navbarContent');
  const profileBtn = document.getElementById('profileDropdown');
  const profileMenu = document.getElementById('profileDropdownMenu');

  toggleBtn?.addEventListener('click', function (e) {
    e.preventDefault();
    navbarContent?.classList.toggle('show');
    const expanded = navbarContent?.classList.contains('show');
    toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  });

  profileBtn?.addEventListener('click', function (e) {
    e.preventDefault();
    profileMenu?.classList.toggle('show');

    if (profileMenu?.classList.contains('show')) {
      navbarContent?.classList.add('profile-open');
    } else {
      navbarContent?.classList.remove('profile-open');
    }
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth > 992) {
      navbarContent?.classList.remove('show');
    }
  });

  const pomodoroBtn = document.getElementById('pomodoroToggleBtn');
  const pomodoroWrapper = document.getElementById('pomodoro-wrapper');

  pomodoroBtn?.addEventListener('click', function (e) {
    e.preventDefault();
    pomodoroWrapper.classList.toggle('visible');
  });
});

document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('globalUserSearch');
  const results = document.getElementById('navbarUserSearchResults');
  let searchTimeout;

  input.addEventListener('input', function () {
    const value = input.value.trim();
    clearTimeout(searchTimeout);

    if (value.length < 2) {
      results.classList.add('d-none');
      return;
    }

    searchTimeout = setTimeout(() => {
      results.classList.remove('d-none');
      results.innerHTML = "<p class='dropdown-item text-muted'>Searching...</p>";

      fetch(`/search-users-global?q=${encodeURIComponent(value)}`)
        .then(r => r.json())
        .then(data => {
          results.innerHTML = '';

          if (!data.length) {
            results.innerHTML = "<p class='dropdown-item text-muted'>No results found</p>";
            return;
          }

          data.forEach(user => {
            const item = document.createElement('a');
            item.className = 'dropdown-item d-flex align-items-center gap-2 py-2';
            item.href = `/user/${user.id}`;
            item.innerHTML = `
              <i class="bi bi-person-circle fs-4 text-secondary"></i>
              <div>
                <div><strong>${user.first_name} ${user.last_name}</strong></div>
                <div class="text-muted small">@${user.username}</div>
              </div>
            `;
            results.appendChild(item);
          });
        })
        .catch(err => {
          results.innerHTML = `<p class='dropdown-item text-danger'>Error: ${err.message}</p>`;
        });
    }, 300);
  });

  // Cierra el dropdown si se hace clic fuera
  document.addEventListener('click', function (e) {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.classList.add('d-none');
    }
  });
});