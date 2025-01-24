from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render

class LoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'accounts/login.html'

    def form_invalid(self, form):
        return render(self.request, self.template_name, {
            'form': form,
            'error_message': form.errors.get('__all__', [''])
        })
