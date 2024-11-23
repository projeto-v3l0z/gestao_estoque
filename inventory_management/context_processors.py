from django.contrib.auth.models import Permission

def user_permissions(request):
    if request.user.is_authenticated:
        return {
            "user_permissions": request.user.get_all_permissions()
        }
    return {"user_permissions": set()}