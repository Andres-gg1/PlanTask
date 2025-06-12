import os
import uuid
from datetime import datetime
from plantask.models.file import File
from plantask.models.activity_log import ActivityLog
from plantask.models.task import TasksFile, TaskCommentsFile
from plantask.models.microtask import MicrotasksFile, MicrotaskCommentsFile
from plantask.models.project import Project
from plantask.models.user import User
import zipfile
import tempfile


ALLOWED_FILES = {'pdf', 'png', 'jpg', 'jpeg', 'jfif'}

class FileUploadService:
    def __init__(self, upload_dir: str, dbsession, user_id: int):
        """
        Initializes the file upload service.

        Parameters:
        - upload_dir (str): Directory path where uploaded files will be saved.
        - dbsession: Active database session (SQLAlchemy).
        - user_id (int): ID of the user uploading the file.
        """
        self.upload_dir = upload_dir
        self.dbsession = dbsession
        self.user_id = user_id
        os.makedirs(self.upload_dir, exist_ok=True)

    def allowed_files(self, extension: str) -> bool:
        """
        Checks whether a file extension is allowed.

        Parameter:
        - extension (str): File extension (without dot).

        Returns:
        - bool: True if allowed, False otherwise.
        """
        return extension.lower() in ALLOWED_FILES

    def save_file_to_disk(self, file_storage) -> dict:
        """
        Saves the uploaded file physically on disk.

        Parameter:
        - file_storage: File object from POST request (e.g., FieldStorage).

        Returns:
        - dict: Metadata about the saved file including original name, path, URL, and extension.
        """
        ext = os.path.splitext(file_storage.filename)[-1].lower().lstrip('.')
        if not self.allowed_files(ext):
            return {"msg":"File type not allowed."}

        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(self.upload_dir, unique_name)

        with open(file_path, 'wb') as f:
            f.write(file_storage.file.read())

        return {
            "filename": file_storage.filename,
            "path": file_path,
            "url": f"/static/uploads/{unique_name}",  
            "extension": ext,
            "unique_name": unique_name
        }

    def handle_upload(self, file_storage, context: dict = None, entity_type: str = None, entity_id: int = None, view_name: str = None) -> dict:
        """
        Handles the complete file upload flow: saving to disk, storing in DB, and logging the activity.

        Parameters:
        - file_storage: File sent by the user.
        - context (dict): Optional dictionary with context info, e.g., {'type': 'task', 'action': 'task_added_file'}.
        - entity_type (str): The type of entity (e.g., 'task', 'microtask', 'project', 'profile').
        - entity_id (int): The ID of the entity the file is related to.
        - view_name (str): Optional name of the view from which the upload is made.

        Returns:
        - dict: Upload result including message, file URL, and file ID in the database.
        """
        try:
            file_info = self.save_file_to_disk(file_storage)

            new_file = File(
                filename=file_info['filename'],
                extension=file_info['extension'],
                route=file_info['url'],
                creation_date=str(datetime.now())
            )
            self.dbsession.add(new_file)
            self.dbsession.flush()

            # Dynamically associate the file with the entity

            # Add other functionalities as new file uploads are added.
            if entity_type == 'task':
                tasks_file = TasksFile(tasks_id=entity_id, files_id=new_file.id)
                log_action = "task_added_file"
                self.dbsession.add(tasks_file)
            elif entity_type == 'microtask':
                microtasks_file = MicrotasksFile(microtasks_id=entity_id, files_id=new_file.id)
                log_action = "microtask_added_file"
                self.dbsession.add(microtasks_file)
            elif entity_type == "project":
                project = self.dbsession.query(Project).filter_by(id = entity_id).first()
                project.project_image_id = new_file.id
                log_action = "project_added_image"
                self.dbsession.flush()
            elif entity_type == "profile_picture":
                user = self.dbsession.query(User).filter_by(id = entity_id).first()
                user.user_image_id = new_file.id
                self.dbsession.flush()

            self.dbsession.flush()

            changes = f"view: {view_name}" if view_name else log_action
            if log_action:
                log = ActivityLog(
                    user_id=self.user_id,
                    task_id=entity_id if entity_type == 'task' else None,
                    microtask_id = entity_id if entity_type == 'microtask' else None,
                    file_id=new_file.id,
                    timestamp=datetime.now(),
                    action=log_action,
                    changes=changes,
                )
                self.dbsession.add(log)
                self.dbession.flush()

            return {
                "bool": True,
                "msg": f"File '{file_info['filename']}' uploaded successfully.",
                "url": file_info["url"],
                "file_id": new_file.id
            }
        except Exception as e:
            return {"bool": False, "msg": f"Upload failed: {str(e)}"}

    def delete_file(self, file_id: int, context:dict = None, view_name: str = None ) -> dict:
        """
        Soft deletes a file by setting its 'active' state to False instead of removing it from disk or database.
        Parameters:
        - file_id (int): ID of the file to be deleted.
        - view_name (str): Optional name of the view from which the delete is made.
        Returns:
        - bool: True if deletion was successful, False otherwise.
        """
        try:
            file_record = self.dbsession.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"bool": False, "msg": "File not found in the database."}
            if not file_record.active:
                return {"bool": False, "msg": "File is already deleted (inactive)."}
            print(f"[DEBUG] Deleting file: {file_record.filename} (ID: {file_id})")
            print(file_record.active)

            file_record.active = False

            log_action = 'task_removed_file'
            if context and context.get('action') == 'task_removed_file':
                log_action = context.get('action')
            action_enum = f"task_removed_file"
            if view_name:
                action_enum += f" | view: {view_name}"
            log = ActivityLog(
                user_id=self.user_id,
                task_id=None,
                file_id=file_id,
                timestamp=datetime.now(),
                action=log_action,
                changes=action_enum,
            )
            self.dbsession.add(log)

            self.dbsession.commit()
            return {"bool": True, "msg": f"File '{file_record.filename}' deleted (set inactive) successfully."}
        except Exception as e:
            return {"bool": False, "msg": f"Error deleting file: {str(e)}"}
        
    def download_file(self, file_id: int) -> dict:
        """
        Retrieves a file from the database and returns its path for downloading.

        Parameters:
        - file_id (int): ID of the file to download.

        Returns:
        - dict: Contains 'bool', 'file_path', 'filename', and optionally 'msg'.
        """
        try:
            file_record = self.dbsession.query(File).filter(File.id == file_id, File.active == True).first()
            if not file_record:
                return {"bool": False, "msg": "File not found or is inactive."}
            
            if not os.path.exists(file_record.route):
                return {"bool": False, "msg": "File does not exist on the server."}

            return {
                "bool": True,
                "file_path": file_record.route,
                "filename": file_record.filename
            }
        except Exception as e:
            return {"bool": False, "msg": f"Error during download: {str(e)}"}
