import uuid
from django.db import models
from django.utils.text import slugify


class CompanyPlan(models.TextChoices):
    FREE = 'free', 'Free'
    STARTER = 'starter', 'Starter'
    PRO = 'pro', 'Pro'
    ENTERPRISE = 'enterprise', 'Enterprise'


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    owner = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT,
        related_name='owned_companies', limit_choices_to={'role': 'organizer'}
    )
    plan = models.CharField(max_length=20, choices=CompanyPlan.choices, default=CompanyPlan.FREE)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    logo_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default='#000000')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies_company'
        verbose_name_plural = 'companies'
        indexes = [
            models.Index(fields=['slug'], name='company_slug_idx'),
            models.Index(fields=['owner', 'is_active'], name='company_owner_active_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CompanyMemberRole(models.TextChoices):
    OWNER = 'owner', 'Owner'
    MANAGER = 'manager', 'Manager'
    STAFF = 'staff', 'Staff'


class CompanyMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=CompanyMemberRole.choices, default=CompanyMemberRole.STAFF)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'companies_member'
        unique_together = ('company', 'user')
        indexes = [
            models.Index(fields=['company', 'role'], name='member_company_role_idx'),
        ]

    def __str__(self):
        return f'{self.user.email} @ {self.company.name} ({self.role})'

# db index reporting
