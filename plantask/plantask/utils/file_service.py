import os
import uuid
from datetime import datetime
from plantask.models.file import File
from plantask.models.activity_log import ActivityLog
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
            "url": f"/static/uploads/a_{unique_name}",
            "extension": ext,
            "unique_name": unique_name
        }

    def handle_upload(self, file_storage, context: dict = None, task_id: int = None) -> dict:
        """
        Handles the complete file upload flow: saving to disk, storing in DB, and logging the activity.

        Parameters:
        - file_storage: File sent by the user.
        - context (dict): Optional dictionary with context info, e.g., {'type': 'task', 'action': 'task_added_file'}.
        - task_id (int): Optional task ID the file is related to.

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
            self.dbsession.flush()

            if context:
                action_enum = f"{context.get('type')} -> {context.get('action')} : <{file_info['url']}>"
                log = ActivityLog(
                    user_id=self.user_id,
                    task_id=task_id,
                    file_id=new_file.id,
                    timestamp=datetime.now(),
                    action=context.get('action'),
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

    def delete_file(self, file_id: int, context:dict = None ) -> dict:
        """
        Deletes a file from the disk and removes its metadata from the database.
        Parameters:
        - file_id (int): ID of the file to be deleted.
        Returns:
        - bool: True if deletion was successful, False otherwise.
        """
        try:
            file_record = self.dbsession.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"bool": False, "msg": "File not found in the database."}

            os.remove(file_record.route)
            self.dbsession.delete(file_record)

            if context:
                action_enum = f"{context.get('type')} -> {context.get('action')} : <{file_record.route}>"
                print(action_enum)
                log = ActivityLog(
                    user_id=self.user_id,
                    task_id=None,
                    file_id=file_id,
                    timestamp=datetime.now(),
                    action=context.get('action'),
                    changes=action_enum,
                )
                self.dbsession.add(log)

            self.dbsession.commit()
            return {"bool": True, "msg": f"File '{file_record.filename}' deleted successfully."}
        except Exception as e:
            return {"bool": False, "msg": f"Error deleting file: {str(e)}"}

    def update_file_metadata(self, file_id: int, new_name: str) -> dict:
        """
        Updates the metadata of a file in the database.
        Parameters:
        - file_id (int): ID of the file to be updated.
        - new_name (str): New name for the file.
        Returns:
        - bool: True if update was successful, False otherwise.
        """
        try:
            file_record = self.dbsession.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"bool": False, "msg": "File not found in the database."}

            ext = os.path.splitext(file_record.route)[1]
            new_unique_name = f"{uuid.uuid4()}{ext}"
            new_path = os.path.join(self.upload_dir, new_unique_name)

            os.rename(file_record.route, new_path)

            old_filename = file_record.filename
            old_path = file_record.route

            file_record.filename = new_name
            file_record.route = new_path
            file_record.creation_date = str(datetime.now()) 

            log = ActivityLog(
                user_id=self.user_id,
                task_id=None,
                file_id=file_id,
                timestamp=datetime.now(),
                action="file_metadata_updated",
                changes=f"Renamed '{old_filename}' -> '{new_name}', path updated from '{old_path}'",
            )
            self.dbsession.add(log)

            self.dbsession.commit()
            return {"bool": True, "msg": f"File metadata updated to '{new_name}'."}
        except Exception as e:
            return {"bool": False, "msg": f"Error updating metadata: {str(e)}"}
        
    def handle_multiple_uploads_as_file(self, file_storages, zip_name="zip_archive.zip", context : dict = None, task_id : int = None) -> dict:
        """
        Handles multiple file uploads, compresses them into a zip file, and saves it to disk.

        Parameters:
        - file_storages: List of file objects from POST request.
        - zip_name (str): Name of the zip file to be created.
        - context (dict): Optional dictionary with context info.

        Returns:
        - dict: Upload result including message and URL of the zip file.
        """
        try:
            if not file_storages:
                return {"bool": False, "msg": "No files to zip found"}
            
            #CREATES A TEMP ZIP ARCHIVE
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

            with zipfile.ZipFile(temp_zip, 'w') as zipf:
                for file_storage in file_storages:
                    ext = os.path.splitext(file_storage.filename)[-1].lower().lstrip('.')
                    if not self.allowed_files(ext):
                        continue #skip not allowed ext files
                    #Read archive contents
                    file_data = file_storage.file.read()
                    zipf.writestr(file_storage.filename, file_data)

            temp_zip.close()

            #Gen an unique name and route for the archive
            unique_name = f"{uuid.uuid4()}.zip"
            final_zip_path = os.path.join(self.upload_dir, unique_name)
            os.rename(temp_zip.name, final_zip_path)

            new_file = File(
                filename=zip_name,
                extension="zip",
                route=final_zip_path,
                creation_date=str(datetime.now())
            )

            self.dbsession.add(new_file)
            self.dbsession.flush()

            if context:
                action_enum = f"{context.get('type')} -> {context.get('action')} : <ZIP:{zip_name}>"
                log = ActivityLog(
                    user_id = self.user_id,
                    task_id=task_id,
                    file_id=new_file.id,
                    timestamp=datetime.now(),
                    action = context.get('action'),
                    changes = action_enum
                )

                self.dbsession.add(log)
            self.dbsession.flush()


            return { 
                "bool": True,
                "msg": f"{len(file_storages)} succesfully compressed archives in '{zip_name}'",
                "url":f"/static/uploads/{unique_name}",
                "file_id":new_file.id
            }
        except Exception as e:
            return {
                "bool":False, 
                "msg": f"Error while compressing archives: {str(e)}"
                }