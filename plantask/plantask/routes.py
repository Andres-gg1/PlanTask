from logging import config


def includeme(config):
    # Static files
    config.add_static_view('static', 'static', cache_max_age=3600)
    
    # Core application routes
    config.add_route('home', '/')
    config.add_route('dashboard', '/dashboard')
    config.add_route('history', '/history')
    
    # Authentication routes
    config.add_route('login', '/login')
    config.add_route('register', '/register')
    config.add_route('logout','/logout')
    config.add_route('validate_ip', '/validate-ip')
    config.add_route('validate_code', '/validate-code')
    config.add_route('invalid_permissions','/invalid-permissions')
    
    # User management routes
    config.add_route('user', r'/user/{id:\d+}')
    config.add_route('edit_user', r'/user/{id:\d+}/edit')
    config.add_route('search_users', '/search-users')
    config.add_route('search_global', '/search-global')
    
    # Project routes
    config.add_route('my_projects', '/projects')
    config.add_route('create_project', '/create-project')
    config.add_route('project_by_id', r'/project/{id:\d+}')
    config.add_route('edit_project', r'/project/{id:\d+}/edit')
    config.add_route('delete_project', r'/project/{id:\d+}/delete')
    config.add_route('project_info', '/project-info')
    config.add_route('kanban_partial', '/project/{id}/kanban_partial')
    
    # Project member management
    config.add_route('add_member', r'/project/{id:\d+}/add-member')
    config.add_route('edit_member', r'/project/{id:\d+}/edit-member')
    config.add_route('remove_member', r'/project/{id:\d+}/remove-member')
    
    # Task routes
    config.add_route('create_task', r'/create-task/{project_id}')
    config.add_route('task_by_id', r'/task/{id:\d+}')
    config.add_route('edit_task', r'/task/{id:\d+}/edit')
    config.add_route('delete_task', r'/task/{id:\d+}/delete')
    config.add_route('update_task_status', '/api/update_task_status')
    
    # Microtask routes
    config.add_route('create_microtask', r'/create-microtask/{task_id}')
    config.add_route('update_microtask_status', '/api/update_microtask_status')
    
    # Label management
    config.add_route('add_label', '/add-label/{project_id}/')
    config.add_route('assign_label_to_task', '/project/{id}/')
    config.add_route('toggle_label_for_task', '/task/{id}/toggle_label')
    config.add_route('edit_label', '/label/edit/{label_id}')
    
    # Comment routes
    config.add_route('add_microtask_comment', r'/add-microtask-comment/{microtask_id:\d+}')
    config.add_route('get_microtask_comments', '/microtask/comments')
    config.add_route('add_task_comment', r'/add-task-comment/{task_id:\d+}')
    config.add_route('get_task_comments', '/task/comments')
    
    # Chat and messaging routes
    config.add_route('chats', '/chats')
    config.add_route('get_chat_messages', r'/get-chat-messages/{chat_id:\d+}')
    config.add_route('get_group_chat_messages', r'/get-group-chat-messages/{chat_id:\d+}')
    config.add_route('send_message', '/send-message')
    config.add_route('create_message_relation', '/send-message-to')
    config.add_route('create_group_chat', '/create-group-chat')
    config.add_route('edit_group_name', '/edit-group-name/{group_id}')
    config.add_route('edit_group_description', '/edit-group-description/{group_id}')
    config.add_route('edit_group_image', '/edit-group-image/{group_id}')
    config.add_route('add_group_members', '/add-group-members')
    config.add_route('search_group_users', '/search-group-users')
    config.add_route('remove_group_member', '/remove-group-member')

    # Notification routes
    config.add_route('get_notifications', '/get-notifications')
    
    # File management routes
    config.add_route('file_crud', '/files')
    config.add_route('file_list_page', '/test/list')
    config.add_route('request_download', '/file/request-download')
    config.add_route('download_file', '/test/download')
    config.add_route('file_upload_page', '/test/upload')
    config.add_route('delete_file_page', '/test/delete')
    config.add_route('multi_upload', '/test/multi_upload')
    
    # Charts and analytics routes
    config.add_route('tasks_charts', '/project/dashboard/{project_id}')
    config.add_route('tasks_completed', '/tasks-completed/{project_id}')

    config.add_route('calendar', '/calendar')
    config.add_route('api_tasks', '/api/tasks')
    config.add_route('api_update_task_status', '/api/update_task_status')
    config.add_route('api_user_tasks', '/api/user_tasks')
    config.add_route('api_update_task_due_date', '/api/update_task_due_date')



