from typing import Any
from django import forms 
from .constants import GENDER_TYPE ,ACCOUNT_TYPE
from django.contrib.auth.models import User 
from .models import UserAddress,UserBankAccount
from django.contrib.auth.forms import UserCreationForm  
from django.contrib.auth.forms import PasswordChangeForm

class UserRegistrationForm(UserCreationForm):
    birth_day = forms.DateTimeField(widget=forms.DateInput(attrs={'type':'date'}))
    gender = forms.ChoiceField( choices=GENDER_TYPE)
    account_type = forms.ChoiceField( choices=ACCOUNT_TYPE)
   
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=120)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100)
    class Meta:
        model = User 
        fields = ['username','first_name','last_name','email','account_type','birth_day','gender', 'street_address','postal_code','city','country','password1','password1']
        
    def save(self,commit=True):
        cur_user = super().save(commit=False)   
        if commit:
            cur_user.save()
            account_type= self.cleaned_data.get('account_type')
            gender= self.cleaned_data.get('gender')
            postal_code= self.cleaned_data.get('postal_code')
            country= self.cleaned_data.get('country')
            birth_day= self.cleaned_data.get('birth_day')
            city= self.cleaned_data.get('city')
            street_address = self.cleaned_data.get('street_address')
            
            
            UserAddress.objects.create(
                user = cur_user,
                country= country,
                city=city,
                street_address=street_address,
                postal_code= postal_code,
                
            )
            
            UserBankAccount.objects.create(
                user = cur_user,
                account_type=account_type,
                gender=gender,
                birth_day=birth_day,
                account_no = 100000+ cur_user.id
                
            )
        return cur_user
    
# this is use for input field style 

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class':(
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })
            
            
            
            
            
class UserUpdateForm(forms.ModelForm):
    birth_day = forms.DateTimeField(widget=forms.DateInput(attrs={'type':'date'}))
    gender = forms.ChoiceField( choices=GENDER_TYPE)
    account_type = forms.ChoiceField( choices=ACCOUNT_TYPE)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=120)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100) 

    class Meta:
        model = User
        fields = ['first_name','last_name','email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })
        # jodi user er account thake 
        if self.instance:
            try:
                user_account = self.instance.account
                user_address = self.instance.address
            except UserBankAccount.DoesNotExist:
                user_account = None
                user_address = None

            if user_account:
                self.fields['account_type'].initial = user_account.account_type
                self.fields['gender'].initial = user_account.gender
                self.fields['birth_day'].initial = user_account.birth_day
                self.fields['street_address'].initial = user_address.street_address
                self.fields['city'].initial = user_address.city
                self.fields['postal_code'].initial = user_address.postal_code
                self.fields['country'].initial = user_address.country

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

            user_account, created = UserBankAccount.objects.get_or_create(user=user) # jodi account thake taile seta jabe user_account ar jodi account na thake taile create hobe ar seta created er moddhe jabe
            user_address, created = UserAddress.objects.get_or_create(user=user) 

            user_account.account_type = self.cleaned_data['account_type']
            user_account.gender = self.cleaned_data['gender']
            user_account.birth_day = self.cleaned_data['birth_day']
            user_account.save()

            user_address.street_address = self.cleaned_data['street_address']
            user_address.city = self.cleaned_data['city']
            user_address.postal_code = self.cleaned_data['postal_code']
            user_address.country = self.cleaned_data['country']
            user_address.save()

        return user
    
class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    'class': (
                        'appearance-none block w-full bg-gray-200 '
                        'text-gray-700 border border-gray-200 rounded '
                        'py-3 px-4 leading-tight focus:outline-none '
                        'focus:bg-white focus:border-gray-500'
                    )
                }
            )