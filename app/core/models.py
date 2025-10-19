# from django.db import models
#
#

from django.db import models
from app.core.tenant_middleware import get_current_tenant


class Upload(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField()


class TenantManager(models.Manager):
    def get_queryset(self):
        tenant_id = get_current_tenant()
        qs = super().get_queryset()
        if tenant_id is None:
            return qs.none()  # safer default
        return qs.filter(tenant_id=tenant_id)


class TenantAwareModel(models.Model):
    tenant_id = models.IntegerField(editable=False, null=True, blank=True)
    # Ensure all queries are auto-filtered by current tenant
    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            self.tenant_id = get_current_tenant()
        super().save(*args, **kwargs)


class Company(models.Model):
    name = models.CharField(max_length=255)
    COMPANY_TYPE_CHOICES = [
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
    ]
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, default='wholesale')

    def __str__(self):
        return self.name
