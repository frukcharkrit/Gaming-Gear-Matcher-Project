# APP01/urls.py
from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # --- Guest & Common Features ---
    path('', views.home_guest, name='home_guest'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    
    # Matching Core

    path('matching-result/', views.matching_result, name='matching_result'),
    path('matching-result/submit-rating/', views.submit_rating, name='submit_rating'),
    
    # Wizard Flow
    path('upload-image/', views.upload_image_and_match, name='upload_image'), # Legacy/Profile support
    path('start-matching/', views.start_matching, name='start_matching'),
    path('wizard/quiz/', views.wizard_quiz, name='wizard_quiz'),
    path('wizard/process-quiz/', views.process_quiz, name='process_quiz'),
    path('wizard/select/<str:category>/', views.wizard_select_gear, name='wizard_select_gear'),
    path('wizard/add/<int:gear_id>/', views.wizard_add_gear, name='wizard_add_gear'),
    path('wizard/remove/<int:gear_id>/', views.wizard_remove_gear, name='wizard_remove_gear'),
    path('wizard/load-preset/<str:variant_name>/', views.wizard_load_preset, name='wizard_load_preset'),

    
    # Temporary Preset Editing (Session based)
    path('matching-result/edit-preset/<str:action>/<int:gear_id>/', views.edit_temp_preset, name='edit_temp_preset_with_id'),
    path('matching-result/edit-preset/<str:action>/', views.edit_temp_preset, name='edit_temp_preset_no_id'),

    # Information & Search
    path('search/', views.global_search, name='global_search'),
    path('gear/<int:gear_id>/', views.gear_detail, name='gear_detail'),
    path('pro-player/<int:player_id>/', views.pro_player_detail, name='pro_player_detail'),
    path('search/gear/', views.search_gear, name='search_gear'),
    path('search/pro-player/', views.search_pro_player, name='search_pro_player'),

    # --- Member Features ---
    path('member/home/', views.home_member, name='home_member'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Presets Management (Database)
    path('presets/', views.manage_presets, name='manage_presets'),
    path('preset/save/', views.save_preset, name='save_preset'),
    path('preset/<int:preset_id>/', views.preset_detail, name='preset_detail'),
    path('preset/<int:preset_id>/edit/', views.edit_preset, name='edit_preset'),
    path('preset/<int:preset_id>/edit-name/', views.edit_preset_name, name='edit_preset_name'),
    path('preset/<int:preset_id>/delete/', views.delete_preset, name='delete_preset'),
    path('preset/<int:preset_id>/rate/', views.submit_preset_rating, name='rate_preset'), # NEW
    path('preset/use-all/<int:player_id>/', views.use_all_gears, name='use_all_gears'),
    
    # Replace Gear in Preset
    path('preset/<int:preset_id>/replace-gear/<int:old_gear_id>/', views.replace_gear, name='replace_gear'),
    path('preset/<int:preset_id>/replace-gear/<int:old_gear_id>/with/<int:new_gear_id>/', views.confirm_replace, name='confirm_replace'),
    
    # Share Preset
    path('preset/<int:preset_id>/share/', views.share_preset, name='share_preset'),
    path('share/<str:share_link>/', views.view_shared_preset, name='view_shared_preset'),

    # --- Admin Features ---
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/users/edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),

    # Admin: Pro Players
    path('admin-dashboard/pro-players/', views.admin_pro_players, name='admin_pro_players'),
    path('admin-dashboard/pro-players/add/', views.admin_add_pro_player, name='admin_add_pro_player'),
    path('admin-dashboard/pro-players/<int:player_id>/edit/', views.admin_edit_pro_player, name='admin_edit_pro_player'),
    path('admin-dashboard/pro-players/<int:player_id>/delete/', views.admin_delete_pro_player, name='admin_delete_pro_player'),

    # Admin: Gaming Gears (แก้ไขชื่อให้ตรงกับ views.py)
    path('admin-dashboard/gears/', views.admin_gears, name='admin_gears'),
    path('admin-dashboard/gears/add/', views.admin_add_gear, name='admin_add_gear'),
    path('admin-dashboard/gears/<int:gear_id>/edit/', views.admin_edit_gear, name='admin_edit_gear'),
    path('admin-dashboard/gears/<int:gear_id>/delete/', views.admin_delete_gear, name='admin_delete_gear'),
    

    
    # Admin: Members Management (แก้ไขให้ตรงกับ views.py)
    path('admin-dashboard/members/', views.admin_members, name='admin_members'),
    path('admin-dashboard/members/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),

    # Admin: Alerts
    path('admin-dashboard/alerts/<int:alert_id>/mark-read/', views.mark_alert_read, name='mark_alert_read'),
    
    # Admin: Password Requests
    path('admin-dashboard/password-requests/', views.admin_password_requests, name='admin_password_requests'),
    path('admin-dashboard/password-requests/<int:request_id>/approve/', views.approve_password_request, name='approve_password_request'),

    # User Messages (Notifications)
    path('profile/messages/', views.user_messages, name='user_messages'),
    path('message/read/<int:notification_id>/', views.mark_message_read, name='mark_message_read'),
    
    # Admin Delete User
    # Admin Delete User
    path('admin-dashboard/users/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    
    # --- API Endpoints ---
    # Association Rules API
    path('api/recommendations/', api_views.api_gear_recommendations, name='api_gear_recommendations'),
    path('api/admin/refresh-rules/', api_views.api_refresh_association_rules, name='api_refresh_association_rules'),
]