def is_tablet_user(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return False
    try:
        return bool(user.profile.is_tablet_user)
    except Exception:
        return False
