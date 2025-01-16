from django.shortcuts import render
from django.views.generic import FormView
from .forms import UserRegistrationForm ,UserUpdateForm
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import RedirectView
from django.contrib import messages
from django.template.loader import render_to_string
from .forms import UserPasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import EmailMultiAlternatives
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

def send_pass_change_mail(user,subject,template):
    mail_subject=subject
    message=render_to_string(template,{
        'user':user,
        })
    send_email=EmailMultiAlternatives(mail_subject,'',to=[user.email])
    send_email.attach_alternative(message,"text/html")
    send_email.send()


class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('home')
    
    def form_valid(self,form):
        print(form.cleaned_data)
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Account created fo successfully.')

        return super().form_valid(form) 
    

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
        messages.success(self.request, f'Logged successfully. ')
        return reverse_lazy('home')
    
class LogoutView(LoginRequiredMixin, RedirectView):
    url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'You have been logged out successfully!')
        return super().get(request, *args, **kwargs)


class UserBankAccountUpdateView(View):
        template_name = 'accounts/user_profile.html'

        def get(self, request):
            form = UserUpdateForm(instance=request.user)
            return render(request, self.template_name, {'form': form})

        def post(self, request):
            form = UserUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('profile')  
            return render(request, self.template_name, {'form': form})
        

def sent_pass_change_email(user,subject,template):
    message = render_to_string(template,{
        'user':user
    })
    sent_email = EmailMultiAlternatives(subject,'',to=[user.email])
    sent_email.attach_alternative(message,'text/html')
    sent_email.send()
   
    
            
@method_decorator(login_required, name='dispatch')
class UserPasswordChangeView(PasswordChangeView):
    form_class = UserPasswordChangeForm
    template_name = 'accounts/user_password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        subject = 'Password Change Successful'
        template = 'accounts/password_change_mail.html'
        send_pass_change_mail(self.request.user, subject, template)
        return super().form_valid(form)