import os
import uuid
from datetime import datetime
from plantask.models.file import File
from plantask.models.activity_log import ActivityLog
from plantask.models.task import TasksFile  # <-- Add this import
import zipfile
import tempfile


ALLOWED_FILES = {'pdf', 'png', 'jpg', 'jpeg'}

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
            raise ValueError("File type not allowed.")

        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(self.upload_dir, unique_name)

        with open(file_path, 'wb') as f:
            f.write(file_storage.file.read())

        return {
            "filename": file_storage.filename,
            "path": file_path,
            "url": f"/static/uploads/{unique_name}",  # No 'a_' prefix unless you want it
            "extension": ext,
            "unique_name": unique_name
        }

    def handle_upload(self, file_storage, context: dict = None, task_id: int = None, view_name: str = None) -> dict:
        """
        Handles the complete file upload flow: saving to disk, storing in DB, and logging the activity.
        Parameters:
        - file_storage: File sent by the user.
        - context (dict): Optional dictionary with context info, e.g., {'type': 'task', 'action': 'task_added_file'}.
        - task_id (int): Optional task ID the file is related to.
        - view_name (str): Optional name of the view from which the upload is made.
        Returns:
        - dict: Upload result including message, file URL, and file ID in the database.
        """
        try:
            file_info = self.save_file_to_disk(file_storage)

            new_file = File(
                filename=file_info['filename'],
                extension=file_info['extension'],
                route=file_info['path'],
                creation_date=str(datetime.now())
            )
            self.dbsession.add(new_file)
            self.dbsession.flush()  # new_file.id is now available

            # Create the relationship in TasksFile if task_id is provided
            if task_id:
                tasks_file = TasksFile(tasks_id=task_id, files_id=new_file.id)
                self.dbsession.add(tasks_file)
                self.dbsession.flush()

            # Use enums for action (only those in activity_log.py)
            log_action = 'task_added_file' if task_id else 'task_added_file'
            if context and context.get('action') in ['task_added_file', 'task_removed_file']:
                log_action = context.get('action')
            action_enum = f"task_added_file"
            if view_name:
                action_enum += f" | view: {view_name}"
            log = ActivityLog(
                user_id=self.user_id,
                task_id=task_id,
                file_id=new_file.id,
                timestamp=datetime.now(),
                action=log_action,
                changes=action_enum,
            )
            self.dbsession.add(log)

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
            print("HOLA")
            print(f"[DEBUG] Deleting file: {file_record.filename} (ID: {file_id})")
            print(file_record.active)
            file_record.active = False

            # Use enums for action (only those in activity_log.py)
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