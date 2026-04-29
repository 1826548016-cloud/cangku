from users.models import AuditLog

def log_action(user, action, resource, description, request=None):
    if not user or not user.is_authenticated:
        return
    
    from users.serializers import ensure_user_profile
    profile = ensure_user_profile(user)
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        team=profile.team,
        user=user,
        action=action,
        resource=resource,
        description=description,
        ip_address=ip_address
    )
