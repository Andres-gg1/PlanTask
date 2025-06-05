function setupKanbanDragAndDrop() {
    const cards = document.querySelectorAll('[draggable="true"]');
    const columns = document.querySelectorAll('.kanban-tasks');

    let draggedCard = null;

    cards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            draggedCard = card;
            e.dataTransfer.setData('text/plain', card.dataset.taskId);
        });
    });

    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        column.addEventListener('drop', async (e) => {
            e.preventDefault();

            const newStatus = column.closest('.kanban-column').dataset.status;
            const taskId = e.dataTransfer.getData('text/plain');

            const card = document.querySelector(`[data-task-id="${taskId}"]`);
            if (card && column !== card.parentElement) {
                column.appendChild(card); // Move instantly

                try {
                    const response = await fetch(window.updateTaskStatusURL, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': window.csrfToken
                        },
                        body: JSON.stringify({
                            task_id: taskId,
                            new_status: newStatus
                        })
                    });

                    const kanbanResponse = await fetch(window.kanbanPartialURL);
                    if (kanbanResponse.ok) {
                        const kanbanHtml = await kanbanResponse.text();
                        document.getElementById('kanban-board-wrapper').innerHTML = kanbanHtml;
                        setupKanbanDragAndDrop();
                    } else {
                        location.reload();
                    }
                } catch (err) {
                    alert("Error updating task status. Reloading board...");
                    location.reload();
                }
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', setupKanbanDragAndDrop);
