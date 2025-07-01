def get_client_ip(request):
    """Get the real client IP address from request headers"""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For format: client, proxy1, proxy2, ...
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr
