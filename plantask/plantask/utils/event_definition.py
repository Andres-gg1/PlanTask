class UserAddedToProjectEvent:
    def __init__(self, request, project_id, user_id):
        self.request = request
        self.project_id = project_id
        self.user_id = user_id
