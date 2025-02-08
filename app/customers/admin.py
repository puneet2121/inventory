from django.contrib import admin

from app.customers import models

# Register your models here.
admin.site.register(models.Customer)
