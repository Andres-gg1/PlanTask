document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'en',
    height: 'auto', // or a number like 400
    events: function(fetchInfo, successCallback, failureCallback) {
      fetch('/api/user_tasks')
        .then(res => res.json())
        .then(data => {
          successCallback(data.tasks || []);
        })
        .catch(failureCallback);
    },
    editable: true, // Enable dragging
    eventClick: function(info) {
      const modal = new bootstrap.Modal(document.getElementById('statusModal'));
      document.getElementById('taskId').value = info.event.id;
      document.getElementById('taskStatus').value = info.event.extendedProps.status;
      modal.show();
    },
    eventDrop: function(info) {
      // Send the new date to the backend
      fetch('/api/update_task_due_date', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: info.event.id, due_date: info.event.startStr })
      })
      .then(res => res.json())
      .then(data => {
        if (data.status !== 'ok') {
          alert('Error updating date.');
          info.revert();
        }
      })
      .catch(() => {
        alert('Error updating date.');
        info.revert();
      });
    }
  });

  calendar.render();

  document.getElementById('statusForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const taskId = document.getElementById('taskId').value;
    const newStatus = document.getElementById('taskStatus').value;

    fetch('/api/update_task_status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: taskId, status: newStatus })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
        calendar.refetchEvents();
      } else {
        alert('Error updating status.');
      }
    });
  });
});
