class UserAddedToProjectEvent:
    def __init__(self, request, project_id, user_id):
        self.request = request
        self.project_id = project_id
        self.user_id = user_id

class UserRemovedFromProjectEvent:
    def __init__(self, request, project_id, user_id):
        self.request = request
        self.project_id = project_id
        self.user_id = user_id

class TaskReadyForReviewEvent:
    def __init__(self, request, task_id):
        self.request = request
        self.task_id = task_id
