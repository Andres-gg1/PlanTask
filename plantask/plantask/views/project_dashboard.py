from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
from plantask.models.project import Project
from plantask.models.task import Task
from plantask.models.label import Label, LabelsTask
from plantask.auth.verifysession import verify_session
from collections import Counter


@view_config(route_name='tasks_charts', renderer='/templates/testing_charts.jinja2', request_method='GET')
@verify_session
def show_tasks(request):
    project_id = request.matchdict.get('project_id')
    project = request.dbsession.query(Project).get(project_id)
    if not project:
        raise HTTPNotFound("Project not found")

    statuses = ['assigned', 'in_progress', 'under_review', 'completed']
    chart_labels = ['Assigned', 'In Progress', 'Under Review', 'Completed']
    chart_data = []
    tasks_by_status = {}

    for status in statuses:
        tasks = request.dbsession.query(Task).filter(
            Task.project_id == project_id,
            Task.status == status,
            Task.active == True
        ).all()
        chart_data.append(len(tasks))

        tasks_by_status[status.replace('_', ' ').title()] = [
            {
                'name': t.task_title,
                'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else 'Sin fecha'
            }
            for t in tasks
        ]

    tasks_by_status_and_label = {}
    for status in statuses:
        label_counts = {}
        tasks = request.dbsession.query(Task).filter(
            Task.project_id == project_id,
            Task.status == status,
            Task.active == True
        ).all()
        for task in tasks:

            labels = request.dbsession.query(Label).join(LabelsTask, LabelsTask.labels_id == Label.id)\
                .filter(LabelsTask.tasks_id == task.id).all()
            for label in labels:
                label_counts[label.label_name] = label_counts.get(label.label_name, 0) + 1
        tasks_by_status_and_label[status] = label_counts

    project_labels = request.dbsession.query(Label).filter(Label.project_id == project_id).all()
    label_colors = {label.label_name: label.label_hex_color for label in project_labels}

    tasks_due_dates = (
        request.dbsession.query(Task.due_date)
        .filter(Task.project_id == project_id, Task.active == True, Task.due_date != None)
        .all()
    )
    due_dates = [t[0].strftime('%Y-%m-%d') for t in tasks_due_dates if t[0]]
    due_dates_counter = Counter(due_dates)

    due_dates_sorted = sorted(due_dates_counter.items())

    return {
        'project': project,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'tasks_by_status_json': tasks_by_status,
        'tasks_by_status_and_label': tasks_by_status_and_label,
        'testing_charts': 'Dashboard',
        'label_colors': label_colors,
        'due_dates_labels': [d[0] for d in due_dates_sorted],
        'due_dates_counts': [d[1] for d in due_dates_sorted],
        'due_dates_heatmap': dict(due_dates_counter),
        'due_dates_heatmap_echarts': [[k, v] for k, v in due_dates_counter.items()],
    }




