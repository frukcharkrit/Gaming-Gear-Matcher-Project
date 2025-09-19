# APP01/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- Guest & Common Features ---
    path('', views.home_guest, name='home_guest'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('upload-image/', views.upload_image_and_match, name='upload_image'),
    path('matching-result/', views.matching_result, name='matching_result'),
    path('gear/<int:gear_id>/', views.gear_detail, name='gear_detail'),
    path('pro-player/<int:player_id>/', views.pro_player_detail, name='pro_player_detail'),
    path('search/gear/', views.search_gear, name='search_gear'),
    path('search/pro-player/', views.search_pro_player, name='search_pro_player'),

    # --- Member Features ---
    path('member/home/', views.home_member, name='home_member'),
    path('match/rate/', views.rate_match, name='rate_match'),
    path('presets/', views.manage_presets, name='manage_presets'),
    path('preset/save/', views.save_preset, name='save_preset'),
    path('preset/<int:preset_id>/', views.preset_detail, name='preset_detail'),
    path('preset/<int:preset_id>/edit/', views.edit_preset, name='edit_preset'),
    path('preset/<int:preset_id>/delete/', views.delete_preset, name='delete_preset'),
    path('preset/<int:preset_id>/share/', views.share_preset, name='share_preset'),
    path('share/<str:share_link>/', views.view_shared_preset, name='view_shared_preset'),
    path('matching-result/edit-preset/<str:action>/<int:gear_id>/', views.edit_temp_preset, name='edit_temp_preset_with_id'),
    path('matching-result/edit-preset/<str:action>/', views.edit_temp_preset, name='edit_temp_preset_no_id'),

    # --- Admin Features ---
    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    # Pro Players
    path('admin/pro-players/', views.admin_pro_players, name='admin_pro_players'),
    path('admin/pro-players/add/', views.admin_add_pro_player, name='admin_add_pro_player'),
    path('admin/pro-players/<int:player_id>/edit/', views.admin_edit_pro_player, name='admin_edit_pro_player'),
    path('admin/pro-players/<int:player_id>/delete/', views.admin_delete_pro_player, name='admin_delete_pro_player'),

    # Gaming Gears
    path('admin/gaming-gears/', views.admin_gaming_gears, name='admin_gaming_gears'),
    path('admin/gaming-gears/add/', views.admin_add_gaming_gear, name='admin_add_gaming_gear'),
    path('admin/gaming-gears/<int:gear_id>/edit/', views.admin_edit_gaming_gear, name='admin_edit_gaming_gear'),
    path('admin/gaming-gears/<int:gear_id>/delete/', views.admin_delete_gaming_gear, name='admin_delete_gaming_gear'),
    
    # AI Models
    path('admin/ai-models/', views.admin_ai_models, name='admin_ai_models'),
    path('admin/ai-models/add/', views.admin_add_ai_model, name='admin_add_ai_model'),
    path('admin/ai-models/<int:model_id>/edit/', views.admin_edit_ai_model, name='admin_edit_ai_model'),
    path('admin/ai-models/<int:model_id>/delete/', views.admin_delete_ai_model, name='admin_delete_ai_model'),
    path('admin/ai-models/<int:model_id>/set-active/', views.admin_set_active_ai_model, name='admin_set_active_ai_model'),
    path('admin/ai-models/<int:model_id>/train/', views.admin_train_ai_model, name='admin_train_ai_model'),
    
    # Users
    # APP01/urls.py
# ...
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
# ...

    # Alerts
    path('admin/alerts/', views.view_alerts, name='view_alerts'),
    path('admin/alerts/<int:alert_id>/mark-read/', views.mark_alert_read, name='mark_alert_read'),
]