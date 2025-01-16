from django.contrib import admin
from .models import IsBankrupt

class IsBankruptAdmin(admin.ModelAdmin):
    list_display = ('is_bankrupt',)  

admin.site.register(IsBankrupt, IsBankruptAdmin)
