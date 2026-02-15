from django.contrib import admin
from .models import GamingGear, ProPlayer, Game, ProPlayerGear, Preset, PresetGear, Role, User

# Register your models here.
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(GamingGear)
class GamingGearAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'brand', 'price')
    list_filter = ('type', 'brand')
    search_fields = ('name', 'brand')

@admin.register(ProPlayer)
class ProPlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'edpi', 'sensitivity')
    list_filter = ('game',)
    search_fields = ('name',)

@admin.register(ProPlayerGear)
class ProPlayerGearAdmin(admin.ModelAdmin):
    list_display = ('player', 'gear')
    search_fields = ('player__name', 'gear__name')

@admin.register(Preset)
class PresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')

@admin.register(PresetGear)
class PresetGearAdmin(admin.ModelAdmin):
    list_display = ('preset', 'gear', 'order')
