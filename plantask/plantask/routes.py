def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('validate_ip', '/validate-ip')
    config.add_route('validate_code', '/validate-code')
    config.add_route('register', '/register')
    config.add_route('invalid_permissions','/invalid-permissions')
    
    