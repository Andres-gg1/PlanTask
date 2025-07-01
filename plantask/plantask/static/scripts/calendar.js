document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'en',
    height: 'auto',
    displayEventTime: false, // Remove time display
    displayEventEnd: false,  // Remove end time display
    events: function(fetchInfo, successCallback, failureCallback) {
      fetch('/api/user_tasks')
        .then(res => res.json())
        .then(data => {
          // Transform the data to include CSS classes based on status and editable by role
          const transformedEvents = (data.tasks || []).map(task => ({
            id: task.id,
            title: task.title,
            start: task.start,
            extendedProps: {
              project_id: task.project_id,
              status: task.status,
              is_project_manager: task.is_project_manager
            },
            className: `status-${task.status}`,
            editable: !!task.is_project_manager // Only project managers can drag
          }));
          successCallback(transformedEvents);
        })
        .catch(failureCallback);
    },
    editable: true, // Calendar is editable, but per-event editable is set above
    eventClick: function(info) {
      const taskId = info.event.id;
      const projectId = info.event.extendedProps.project_id;
      window.location.href = `/task/${taskId}`;
    },
    eventDrop: function(info) {
      // Prevent drop if not project_manager
      if (!info.event.extendedProps.is_project_manager) {
        alert('No tienes permiso para mover esta tarea.');
        info.revert();
        return;
      }
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
});
