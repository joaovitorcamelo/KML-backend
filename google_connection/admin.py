from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["upper_case", "user_key"]
    fields = ["email", "user_key"]
    readonly_fields = ["user_key"]
    list_filter = ["email"]
    ordering = ["email"]
    search_fields = ["email"]

    @admin.display(description="Email")
    def upper_case(self, obj):
        return f"{obj.email}".lower()
