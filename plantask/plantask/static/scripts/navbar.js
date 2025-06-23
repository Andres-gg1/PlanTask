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
          
          // Group results by type
          const users = data.filter(item => item.type === 'user');
          const projects = data.filter(item => item.type === 'project');
          
          // Add section headers and results
          if (users.length > 0) {
            results.innerHTML += '<h6 class="dropdown-header">Users</h6>';
            users.forEach(user => {
              const item = document.createElement('a');
              item.className = 'dropdown-item d-flex align-items-center gap-2 py-2';
              item.href = `/user/${user.id}`;
              const pfp = user.image_route
                ? `<img src="${user.image_route}" alt="PFP" class="rounded-circle" style="width: 32px; height: 32px; object-fit: cover;">`
                : `<i class="bi bi-person-circle fs-4 text-secondary"></i>`;

              item.innerHTML = `
                ${pfp}
                <div>
                  <div><strong>${user.first_name} ${user.last_name}</strong></div>
                  <div class="text-muted small">@${user.username}</div>
                </div>
              `;

              results.appendChild(item);
            });
          }
          
          if (projects.length > 0) {
            // Add divider if we already have users
            if (users.length > 0) {
              const divider = document.createElement('div');
              divider.className = 'dropdown-divider';
              results.appendChild(divider);
            }
            
            results.innerHTML += '<h6 class="dropdown-header">Projects</h6>';
            projects.forEach(project => {
              const item = document.createElement('a');
              item.className = 'dropdown-item d-flex align-items-center gap-2 py-2';
              item.href = `/project/${project.id}`;
              const icon = project.image_route
                ? `<img src="${project.image_route}" alt="Project" class="rounded" style="width: 32px; height: 32px; object-fit: cover;">`
                : `<img src="/static/img_example.jpg" alt="Project" class="rounded" style="width: 32px; height: 32px; object-fit: cover;">`

              item.innerHTML = `
                ${icon}
                <div>
                  <div><strong>${project.name}</strong></div>
                  <div class="text-muted small">${project.description}</div>
                </div>
              `;

              results.appendChild(item);
            });
          }
        })
        .catch(err => {
          results.innerHTML = `<p class='dropdown-item text-danger'>Error: ${err.message}</p>`;
        });
    }, 300);
  });

  document.addEventListener('click', function (e) {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.classList.add('d-none');
    }
  });
});