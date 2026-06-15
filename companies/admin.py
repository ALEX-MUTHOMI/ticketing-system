from django.contrib import admin
from .models import Company, CompanyMember


class CompanyMemberInline(admin.TabularInline):
    model = CompanyMember
    extra = 0
    readonly_fields = ('joined_at',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'plan', 'is_active', 'created_at')
    list_filter = ('plan', 'is_active')
    search_fields = ('name', 'slug', 'owner__email')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [CompanyMemberInline]


@admin.register(CompanyMember)
class CompanyMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('user__email', 'company__name')
