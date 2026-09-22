from profileapp.utils import is_tablet_user


def tablet_user(request):
    return {'is_tablet_user': is_tablet_user(request.user)}
