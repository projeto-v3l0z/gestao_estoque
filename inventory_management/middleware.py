import threading
from django.contrib.auth.models import AnonymousUser

# Thread local storage para armazenar o usuário atual
_thread_locals = threading.local()

def get_current_user():
    """
    Retorna o usuário atual do thread local
    """
    return getattr(_thread_locals, 'user', None)

def set_current_user(user):
    """
    Define o usuário atual no thread local
    """
    _thread_locals.user = user

class CurrentUserMiddleware:
    """
    Middleware para capturar o usuário atual e disponibilizá-lo para os signals
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capturar o usuário atual
        if hasattr(request, 'user'):
            set_current_user(request.user)
        else:
            set_current_user(AnonymousUser())
        
        response = self.get_response(request)
        
        # Limpar o thread local após a requisição
        if hasattr(_thread_locals, 'user'):
            delattr(_thread_locals, 'user')
        
        return response
