# APP01/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.files.storage import FileSystemStorage # สำหรับอัปโหลดไฟล์
from django.conf import settings # สำหรับเข้าถึง MEDIA_ROOT
from django.utils import timezone # เพิ่ม import นี้

import json # เพิ่ม import นี้สำหรับ json.loads

from .models import User, Role, ProPlayer, GamingGear, Preset, Rating, AIModel, Alert, ProPlayerGear, PresetGear # นำเข้า Models ของคุณ
from .forms import RegisterForm, ProPlayerForm, GamingGearForm, PresetForm, AIModelForm, RatingForm, LoginForm # เพิ่ม RatingForm

# สำหรับ AI และ Image Processing
import os
import cv2
import numpy as np
# import tensorflow as tf
# from tensorflow.keras.models import load_model # ตัวอย่างการโหลดโมเดล AI

# สมมติฐาน: คุณมีโมเดล AI ที่โหลดได้
# try:
#     # PATH_TO_AI_MODELS = os.path.join(settings.BASE_DIR, 'ai_models')
#     # active_model_instance = AIModel.objects.filter(is_active=True).first()
#     # if active_model_instance:
#     #     AI_MODEL = load_model(os.path.join(PATH_TO_AI_MODELS, active_model_instance.file_path))
#     # else:
#     #     AI_MODEL = None # หรือโหลด default model
#     #     print("No active AI model found. Matching features will be limited.")
#     print("AI model loading is currently commented out for initial setup.")
# except Exception as e:
#     AI_MODEL = None
#     print(f"Error loading AI model: {e}")

# Helper function เพื่อตรวจสอบว่าผู้ใช้เป็น Admin

# Helper function เพื่อตรวจสอบว่าผู้ใช้เป็น Member
def is_member(user):
    return user.is_authenticated and user.role and user.role.role_name == 'Member'

def home_guest(request):
    featured_pro_players = ProPlayer.objects.all()[:5]
    featured_gears = GamingGear.objects.all()[:5]
    context = {
        'featured_pro_players': featured_pro_players,
        'featured_gears': featured_gears,
    }
    return render(request, 'APP01/home_guest.html', context)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST) # ใช้ฟอร์มที่เราสร้างใน forms.py
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'APP01/register.html', {'form': form})

def is_admin(user):
    return user.is_authenticated and user.role and user.role.role_name == 'Admin'

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user) # Use 'login' instead of 'auth_login'
                if is_admin(user):
                    messages.success(request, f'ยินดีต้อนรับ, {user.username}!')
                    return redirect('/admin/')
                else:
                    messages.success(request, f'ยินดีต้อนรับกลับ, {user.username}!')
                    return redirect('home_member')
            else:
                messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
                return render(request, 'APP01/login.html', {'form': form})
        else:
            messages.error(request, 'โปรดกรอกข้อมูลให้ครบถ้วน')
            return render(request, 'APP01/login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'APP01/login.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                from_email=settings.EMAIL_HOST_USER, # ต้องตั้งค่าใน settings.py
                email_template_name='APP01/password_reset_email.html',
                subject_template_name='APP01/password_reset_subject.txt',
            )
            messages.success(request, 'Password reset email has been sent.')
            return redirect('login') # หรือหน้าแจ้งเตือนว่าส่งอีเมลแล้ว
        else:
            messages.error(request, 'Failed to send password reset email.')
    else:
        form = PasswordResetForm()
    return render(request, 'APP01/forgot_password.html', {'form': form})

def upload_image_and_match(request):
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_image = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_image.name, uploaded_image)
        uploaded_file_url = fs.url(filename)

        try:
            image_path = os.path.join(settings.MEDIA_ROOT, filename)
            # Dummy AI Processing for demonstration
            user_physique_vector = [0.1, 0.2, 0.3, 0.4, 0.5] # Simulate AI output
            
            # Find closest ProPlayer
            best_match_player = None
            min_distance = float('inf')

            pro_players = ProPlayer.objects.all()
            for player in pro_players:
                if player.physique_vector:
                    player_vec = json.loads(player.physique_vector) # สมมติเก็บเป็น JSON string
                    # Calculate distance (e.g., Euclidean distance)
                    distance = np.linalg.norm(np.array(user_physique_vector) - np.array(player_vec))
                    if distance < min_distance:
                        min_distance = distance
                        best_match_player = player

            if best_match_player:
                request.session['match_result'] = {
                    'uploaded_image_url': uploaded_file_url,
                    'matched_player_id': best_match_player.player_id,
                    'min_distance': min_distance,
                    'temp_preset_gears': [] # สำหรับแก้ไข preset ชั่วคราว
                }
                return redirect('matching_result')
            else:
                messages.warning(request, "No suitable Pro Player found for matching.")
                return redirect('upload_image')

        except Exception as e:
            messages.error(request, f"Image processing or matching failed: {e}")
            fs.delete(filename) # ลบรูปภาพที่อัปโหลดหากเกิดข้อผิดพลาด
            return redirect('upload_image')
    else:
        messages.error(request, 'Please upload an image.')
    return render(request, 'APP01/upload_image.html') # หน้าสำหรับอัปโหลดรูป


def matching_result(request):
    match_result = request.session.get('match_result')
    if not match_result:
        return redirect('upload_image') # หากไม่มีข้อมูลผลลัพธ์ ให้กลับไปหน้าอัปโหลด

    matched_player = get_object_or_404(ProPlayer, player_id=match_result['matched_player_id'])
    
    # ดึงอุปกรณ์ที่ Pro Player คนนั้นใช้
    pro_player_gears = GamingGear.objects.filter(proplayergear__player=matched_player)

    # จัดการ Temporary Preset
    temp_preset_gears = []
    if 'temp_preset_gears' in match_result:
        for gear_id in match_result['temp_preset_gears']:
            temp_preset_gears.append(get_object_or_404(GamingGear, gear_id=gear_id))
    else: # ถ้ายังไม่มีการแก้ไข temp preset, ให้ใช้ default จาก pro player
        temp_preset_gears = list(pro_player_gears)
        match_result['temp_preset_gears'] = [g.gear_id for g in temp_preset_gears]
        request.session['match_result'] = match_result # อัปเดต session

    # สำหรับการให้คะแนน
    rating_form = None
    if request.user.is_authenticated and request.user.role and request.user.role.role_name == 'Member':
        rating_form = RatingForm() # สร้างฟอร์ม Rating เปล่าๆ

    context = {
        'uploaded_image_url': match_result['uploaded_image_url'],
        'matched_player': matched_player,
        'pro_player_gears': pro_player_gears, # ชุดอุปกรณ์แนะนำของ Pro Player
        'temp_preset_gears': temp_preset_gears, # ชุดอุปกรณ์ที่ผู้ใช้กำลังแก้ไข
        'is_member': request.user.is_authenticated and request.user.role and request.user.role.role_name == 'Member',
        'rating_form': rating_form, # ส่งฟอร์ม Rating ไปยัง template
    }
    return render(request, 'APP01/matching_result.html', context)


# ฟังก์ชันสำหรับแก้ไข Preset ชั่วคราวจากหน้าผลลัพธ์
def edit_temp_preset(request, action, gear_id=None):
    match_result = request.session.get('match_result')
    if not match_result:
        return redirect('upload_image')

    current_temp_gears = match_result.get('temp_preset_gears', [])
    gear_id = int(gear_id) if gear_id else None

    if action == 'add' and gear_id and gear_id not in current_temp_gears:
        current_temp_gears.append(gear_id)
        messages.success(request, 'Gear added to temporary preset.')
    elif action == 'remove' and gear_id and gear_id in current_temp_gears:
        current_temp_gears.remove(gear_id)
        messages.success(request, 'Gear removed from temporary preset.')
    # เพิ่ม action สำหรับ reorder ได้ถ้าต้องการ

    match_result['temp_preset_gears'] = current_temp_gears
    request.session['match_result'] = match_result
    return redirect('matching_result')

def gear_detail(request, gear_id):
    gear = get_object_or_404(GamingGear, gear_id=gear_id)
    context = {
        'gear': gear
    }
    return render(request, 'APP01/gear_detail.html', context)

def pro_player_detail(request, player_id):
    pro_player = get_object_or_404(ProPlayer, player_id=player_id)
    # ดึงอุปกรณ์ที่ Pro Player คนนี้ใช้
    pro_player_gears = GamingGear.objects.filter(proplayergear__player=pro_player)
    context = {
        'pro_player': pro_player,
        'pro_player_gears': pro_player_gears
    }
    return render(request, 'APP01/pro_player_detail.html', context)

def search_gear(request):
    query = request.GET.get('q')
    gears = GamingGear.objects.all()
    if query:
        gears = gears.filter(name__icontains=query) # ค้นหาจากชื่ออุปกรณ์
    context = {
        'gears': gears,
        'query': query
    }
    return render(request, 'APP01/search_gear.html', context)

def search_pro_player(request):
    query = request.GET.get('q')
    pro_players = ProPlayer.objects.all()
    if query:
        pro_players = pro_players.filter(name__icontains=query) # ค้นหาจากชื่อ Pro Player
    context = {
        'pro_players': pro_players,
        'query': query
    }
    return render(request, 'APP01/search_pro_player.html', context)

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest') # ถ้าเป็น admin จะ redirect กลับไปหน้า guest
def home_member(request):
    user_presets = Preset.objects.filter(user=request.user).order_by('-created_at')[:5]
    context = {
        'user_presets': user_presets,
    }
    return render(request, 'APP01/home_member.html', context)

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def save_preset(request):
    match_result = request.session.get('match_result')
    if not match_result or not match_result.get('temp_preset_gears'):
        messages.error(request, 'No temporary preset to save. Please perform a match first.')
        return redirect('upload_image')

    if request.method == 'POST':
        form = PresetForm(request.POST) # Form ที่มีฟิลด์สำหรับ preset_name
        if form.is_valid():
            preset_name = form.cleaned_data['name']
            
            # สร้าง Preset ใหม่
            new_preset = Preset.objects.create(
                user=request.user,
                name=preset_name,
            )
            # เพิ่ม Gear ลงใน Preset
            order_num = 1
            for gear_id in match_result['temp_preset_gears']:
                gear = get_object_or_404(GamingGear, gear_id=gear_id)
                PresetGear.objects.create(preset=new_preset, gear=gear, order=order_num)
                order_num += 1

            # เคลียร์ session
            if 'match_result' in request.session:
                del request.session['match_result']

            messages.success(request, f'Preset "{preset_name}" saved successfully!')
            return redirect('manage_presets')
        else:
            messages.error(request, 'Failed to save preset. Please provide a valid name.')
    else:
        form = PresetForm(initial={'name': f"My Preset {Preset.objects.filter(user=request.user).count() + 1}"})
    
    # แสดงหน้าจอให้ตั้งชื่อ Preset
    return render(request, 'APP01/save_preset.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def submit_rating(request): # เปลี่ยนจาก rate_match เป็น submit_rating
    match_result = request.session.get('match_result')
    if not match_result:
        messages.error(request, 'No match result to rate.')
        return redirect('upload_image')

    matched_player = get_object_or_404(ProPlayer, player_id=match_result['matched_player_id'])

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            # ตรวจสอบว่าผู้ใช้เคยให้คะแนน ProPlayer นี้แล้วหรือยัง
            # คุณอาจจะต้องการให้คะแนนแต่ละ match_session ไม่ใช่แค่ ProPlayer
            # สำหรับตอนนี้จะตรวจสอบ ProPlayer
            existing_rating = Rating.objects.filter(user=request.user, proplayer=matched_player).first()
            if existing_rating:
                messages.warning(request, 'You have already rated this Pro Player for a previous match.')
                # คุณอาจจะให้แก้ไขได้ หรือไม่อนุญาตให้ซ้ำ
            else:
                rating = form.save(commit=False)
                rating.user = request.user
                rating.proplayer = matched_player # กำหนด ProPlayer ที่ถูกให้คะแนน
                rating.save()
                messages.success(request, 'Thank you for your feedback!')
            
            if 'match_result' in request.session:
                del request.session['match_result']
            return redirect('home_member')
        else:
            messages.error(request, 'Error submitting your rating. Please check your input.')
    return redirect('matching_result') # ถ้าไม่ใช่ POST หรือมีข้อผิดพลาด ให้กลับไปหน้าผลลัพธ์

@login_required(login_url='login')
def rate_match(request):
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            # คุณอาจจะต้องเพิ่ม ProPlayer หรือ GamingGear ที่ถูกให้คะแนน
            # rating.proplayer = ...
            # rating.gaming_gear = ...
            rating.save()
            messages.success(request, 'ขอบคุณสำหรับคะแนนของคุณ!')
            return redirect('matching_result')  # หรือหน้าที่เหมาะสม
        else:
            messages.error(request, 'กรุณาให้คะแนนอย่างถูกต้อง')
    return redirect('matching_result')

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def manage_presets(request):
    user_presets = Preset.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'presets': user_presets
    }
    return render(request, 'APP01/manage_presets.html', context)

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def preset_detail(request, preset_id):
    preset = get_object_or_404(Preset, preset_id=preset_id, user=request.user)
    preset_gears = PresetGear.objects.filter(preset=preset).order_by('order')
    context = {
        'preset': preset,
        'preset_gears': preset_gears
    }
    return render(request, 'APP01/preset_detail.html', context)

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def edit_preset(request, preset_id):
    preset = get_object_or_404(Preset, preset_id=preset_id, user=request.user)
    current_gears = list(PresetGear.objects.filter(preset=preset).order_by('order'))

    if request.method == 'POST':
        form = PresetForm(request.POST, instance=preset) # เพื่ออัปเดตชื่อ Preset
        if form.is_valid():
            form.save()
            
            # การจัดการ Gears
            # ผมแนะนำให้ใช้ JavaScript ใน frontend เพื่อส่ง list ของ gear_id ที่เลือกมา
            # ในที่นี้สมมติว่ามีการส่ง 'selected_gears' ซึ่งเป็น list ของ gear_id
            selected_gear_ids = request.POST.getlist('selected_gears') 
            
            # ลบ Gear เก่าทั้งหมดที่เชื่อมกับ Preset นี้
            PresetGear.objects.filter(preset=preset).delete()
            
            # เพิ่ม Gear ใหม่เข้าไปตามลำดับที่ส่งมา
            order_num = 1
            for gear_id in selected_gear_ids:
                gear = get_object_or_404(GamingGear, gear_id=gear_id)
                PresetGear.objects.create(preset=preset, gear=gear, order=order_num)
                order_num += 1
            
            messages.success(request, f'Preset "{preset.name}" updated successfully!')
            return redirect('preset_detail', preset_id=preset.preset_id)
        else:
            messages.error(request, 'Failed to update preset. Please correct the errors.')
    else:
        form = PresetForm(instance=preset)
    
    # Gears ทั้งหมดสำหรับให้ผู้ใช้เลือก
    all_gears = GamingGear.objects.all().order_by('name') 
    
    # IDs ของ Gears ที่อยู่ใน Preset นี้แล้ว
    current_gear_ids = [pg.gear.gear_id for pg in current_gears]

    context = {
        'form': form,
        'preset': preset,
        'current_gears': current_gears, # รายการ PresetGear objects สำหรับแสดงผล
        'all_gears': all_gears, # รายการ GamingGear objects สำหรับตัวเลือก
        'current_gear_ids': current_gear_ids, # IDs สำหรับเช็คใน template
    }
    return render(request, 'APP01/edit_preset.html', context)


@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def delete_preset(request, preset_id):
    preset = get_object_or_404(Preset, preset_id=preset_id, user=request.user)
    if request.method == 'POST':
        preset.delete()
        messages.success(request, f'Preset "{preset.name}" deleted successfully.')
    return redirect('manage_presets') # Redirect หลังจากลบสำเร็จ
    # return render(request, 'APP01/confirm_delete_preset.html', {'preset': preset}) # อาจทำเป็น modal

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def share_preset(request, preset_id):
    preset = get_object_or_404(Preset, preset_id=preset_id, user=request.user)
    if not preset.share_link:
        import uuid
        preset.share_link = str(uuid.uuid4())
        preset.save()
    
    shareable_url = request.build_absolute_uri(f'/share/{preset.share_link}/') # URL สำหรับแชร์
    messages.info(request, f"Shareable link: {shareable_url}")
    return redirect('preset_detail', preset_id=preset.preset_id)

def view_shared_preset(request, share_link):
    preset = get_object_or_404(Preset, share_link=share_link)
    preset_gears = PresetGear.objects.filter(preset=preset).order_by('order')
    context = {
        'preset': preset,
        'preset_gears': preset_gears,
        'is_shared_view': True,
    }
    return render(request, 'APP01/preset_detail.html', context) # ใช้ template เดียวกัน

@login_required(login_url='login')
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home_guest')

# --- Admin Views ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member') # Redirect non-admin to home_member
def admin_dashboard(request):
    total_users = User.objects.count()
    total_pro_players = ProPlayer.objects.count()
    total_gears = GamingGear.objects.count()
    total_presets = Preset.objects.count()
    
    # ดึง Alert ที่ยังไม่อ่าน
    unread_alerts = Alert.objects.filter(is_read=False).order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'total_pro_players': total_pro_players,
        'total_gears': total_gears,
        'total_presets': total_presets,
        'unread_alerts': unread_alerts,
    }
    return render(request, 'APP01/admin_dashboard.html', context)


# --- Admin Pro Players CRUD ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_pro_players(request): # S_Pro_List (เปลี่ยนชื่อจาก manage_pro_players)
    pro_players = ProPlayer.objects.all().order_by('name')
    return render(request, 'APP01/admin_pro_players.html', {'pro_players': pro_players})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_add_pro_player(request): # S_Add_Pro_Player (เปลี่ยนชื่อจาก add_pro_player)
    if request.method == 'POST':
        form = ProPlayerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() # ProPlayerForm.save() จะจัดการ ProPlayerGear ให้
            messages.success(request, 'Pro Player added successfully!')
            return redirect('admin_pro_players')
        else:
            messages.error(request, 'Failed to add Pro Player. Please correct the errors.')
    else:
        form = ProPlayerForm()
    return render(request, 'APP01/admin_pro_player_form.html', {'form': form, 'form_title': 'Add Pro Player'}) # ใช้ form template เดียวกัน

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_edit_pro_player(request, player_id): # S_Edit_Pro_Player (เปลี่ยนชื่อจาก edit_pro_player)
    pro_player = get_object_or_404(ProPlayer, player_id=player_id)
    
    if request.method == 'POST':
        form = ProPlayerForm(request.POST, request.FILES, instance=pro_player)
        if form.is_valid():
            form.save() # ProPlayerForm.save() จะจัดการ ProPlayerGear ให้
            messages.success(request, 'Pro Player updated successfully!')
            return redirect('admin_pro_players')
        else:
            messages.error(request, 'Failed to update Pro Player. Please correct the errors.')
    else:
        form = ProPlayerForm(instance=pro_player)
    
    # สำหรับแสดงผลใน Template (ถ้า ProPlayerForm ไม่ได้จัดการทั้งหมด)
    # current_gears = GamingGear.objects.filter(proplayergear__player=pro_player)
    # all_gears = GamingGear.objects.all()

    context = {
        'form': form,
        'pro_player': pro_player,
        'form_title': 'Edit Pro Player',
        # 'current_gears': current_gears, # ตอนนี้ ProPlayerForm จัดการแล้ว ไม่จำเป็นต้องส่งไป
        # 'all_gears': all_gears,
    }
    return render(request, 'APP01/admin_pro_player_form.html', context) # ใช้ form template เดียวกัน

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_delete_pro_player(request, player_id): # (เปลี่ยนชื่อจาก delete_pro_player)
    pro_player = get_object_or_404(ProPlayer, player_id=player_id)
    if request.method == 'POST':
        name = pro_player.name
        pro_player.delete()
        messages.success(request, f'Pro Player "{name}" deleted successfully.')
    return redirect('admin_pro_players')
    # return render(request, 'APP01/admin_confirm_delete_pro_player.html', {'pro_player': pro_player}) # ทำใน template list แล้ว

# --- Admin Gaming Gears CRUD ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_gaming_gears(request): # (เปลี่ยนชื่อจาก admin_manage_gears)
    gaming_gears = GamingGear.objects.all().order_by('name')
    return render(request, 'APP01/admin_gaming_gears.html', {'gaming_gears': gaming_gears})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_add_gaming_gear(request): # (เปลี่ยนชื่อจาก admin_add_gear)
    if request.method == 'POST':
        form = GamingGearForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gaming Gear added successfully!')
            return redirect('admin_gaming_gears')
        else:
            messages.error(request, 'Failed to add Gaming Gear. Please correct the errors.')
    else:
        form = GamingGearForm()
    return render(request, 'APP01/admin_gaming_gear_form.html', {'form': form, 'form_title': 'Add Gaming Gear'})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_edit_gaming_gear(request, gear_id): # (เปลี่ยนชื่อจาก admin_edit_gear)
    gaming_gear = get_object_or_404(GamingGear, gear_id=gear_id)
    if request.method == 'POST':
        form = GamingGearForm(request.POST, request.FILES, instance=gaming_gear)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gaming Gear updated successfully!')
            return redirect('admin_gaming_gears')
        else:
            messages.error(request, 'Failed to update Gaming Gear. Please correct the errors.')
    else:
        form = GamingGearForm(instance=gaming_gear)
    return render(request, 'APP01/admin_gaming_gear_form.html', {'form': form, 'form_title': 'Edit Gaming Gear'})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_delete_gaming_gear(request, gear_id): # (เปลี่ยนชื่อจาก admin_delete_gear)
    gaming_gear = get_object_or_404(GamingGear, gear_id=gear_id)
    if request.method == 'POST':
        name = gaming_gear.name
        gaming_gear.delete()
        messages.success(request, f'Gaming Gear "{name}" deleted successfully.')
    return redirect('admin_gaming_gears')
    # return render(request, 'APP01/admin_confirm_delete_gear.html', {'gear': gear}) # ทำใน template list แล้ว

# --- Admin User Management ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_users(request): # เปลี่ยนชื่อจาก manage_members
    users = User.objects.all().order_by('username') # แสดง User ทั้งหมด ไม่ใช่แค่ Member
    context = {'users': users} # เปลี่ยนชื่อ key เป็น 'users'
    return render(request, 'APP01/admin_users.html', context) # ต้องสร้าง admin_users.html

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_edit_user(request, user_id): # เปลี่ยนชื่อจาก edit_member
    user_obj = get_object_or_404(User, user_id=user_id)
    # คุณจะต้องสร้าง UserEditForm ใน forms.py เพื่อแก้ไข User, Role, etc.
    # เช่น
    # from .forms import UserEditForm
    # if request.method == 'POST':
    #     form = UserEditForm(request.POST, instance=user_obj)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, 'User updated successfully.')
    #         return redirect('admin_users')
    # else:
    #     form = UserEditForm(instance=user_obj)
    # context = {'form': form, 'user_obj': user_obj, 'form_title': 'Edit User'}
    # return render(request, 'APP01/admin_user_form.html', context)
    messages.info(request, f"Editing user: {user_obj.username} - functionality to be implemented.")
    return redirect('admin_users')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_delete_user(request, user_id): # เปลี่ยนชื่อจาก delete_member
    user_obj = get_object_or_404(User, user_id=user_id)
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'User {username} deleted successfully.')
    return redirect('admin_users')
    # return render(request, 'APP01/admin_confirm_delete_user.html', {'user_obj': user_obj})

# --- Admin AI Model Management ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_ai_models(request): # เปลี่ยนชื่อจาก manage_ai_models
    models = AIModel.objects.all().order_by('-created_at')
    context = {'models': models}
    return render(request, 'APP01/admin_ai_models.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_add_ai_model(request): # เปลี่ยนชื่อจาก add_ai_model
    if request.method == 'POST':
        form = AIModelForm(request.POST, request.FILES)
        if form.is_valid():
            new_model = form.save(commit=False)
            new_model.created_at = timezone.now()
            new_model.last_trained_at = timezone.now()
            new_model.is_active = False # Default to inactive, admin sets active later
            new_model.save()
            messages.success(request, f'AI Model "{new_model.name}" added successfully.')
            return redirect('admin_ai_models')
        else:
            messages.error(request, 'Failed to add AI Model.')
    else:
        form = AIModelForm()
    return render(request, 'APP01/admin_ai_model_form.html', {'form': form, 'form_title': 'Add AI Model'})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_edit_ai_model(request, model_id): # เปลี่ยนชื่อจาก edit_ai_model
    ai_model = get_object_or_404(AIModel, model_id=model_id)
    if request.method == 'POST':
        form = AIModelForm(request.POST, request.FILES, instance=ai_model)
        if form.is_valid():
            form.save()
            messages.success(request, f'AI Model "{ai_model.name}" updated successfully.')
            return redirect('admin_ai_models')
        else:
            messages.error(request, 'Failed to update AI Model.')
    else:
        form = AIModelForm(instance=ai_model)
    return render(request, 'APP01/admin_ai_model_form.html', {'form': form, 'ai_model': ai_model, 'form_title': 'Edit AI Model'})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_delete_ai_model(request, model_id): # เปลี่ยนชื่อจาก delete_ai_model
    ai_model = get_object_or_404(AIModel, model_id=model_id)
    if request.method == 'POST':
        name = ai_model.name
        ai_model.delete()
        messages.success(request, f'AI Model "{name}" deleted successfully.')
    return redirect('admin_ai_models')
    # return render(request, 'APP01/admin_confirm_delete_ai_model.html', {'ai_model': ai_model})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_train_ai_model(request, model_id):
    ai_model = get_object_or_404(AIModel, pk=model_id)
    # ในส่วนนี้คุณจะเรียกใช้ฟังก์ชันสำหรับ Train โมเดล AI ของคุณ
    # เช่น ai_model.train_model() หรือเรียกใช้ Celery task
    messages.success(request, f'กำลังทำการ Train โมเดล {ai_model.name}...')
    return redirect('manage_ai_models')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_member')
def admin_set_active_ai_model(request, model_id): # เปลี่ยนชื่อจาก set_active_ai_model
    if request.method == 'POST':
        AIModel.objects.update(is_active=False) # Set all to inactive
        model_to_activate = get_object_or_404(AIModel, model_id=model_id)
        model_to_activate.is_active = True
        model_to_activate.save()
        messages.success(request, f'AI Model "{model_to_activate.name}" is now active.')
    return redirect('admin_ai_models')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def train_ai_model(request, model_id):
    ai_model = get_object_or_404(AIModel, model_id=model_id)
    if request.method == 'POST':
        # Simulate training process (replace with actual AI training logic)
        messages.info(request, f'AI Model "{ai_model.name}" training started...')
        # In a real scenario, this would trigger a background task
        ai_model.last_trained_at = timezone.now() # Import timezone
        ai_model.save()
        messages.success(request, f'AI Model "{ai_model.name}" training simulated successfully.')
        return redirect('manage_ai_models')
    return render(request, 'APP01/admin_confirm_train_ai_model.html', {'ai_model': ai_model})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def view_alerts(request):
    alerts = Alert.objects.all().order_by('-created_at')
    context = {'alerts': alerts}
    return render(request, 'APP01/admin_alerts.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def mark_alert_read(request, alert_id):
    alert = get_object_or_404(Alert, alert_id=alert_id)
    if request.method == 'POST':
        alert.is_read = True
        alert.save()
        messages.success(request, 'Alert marked as read.')
    return redirect('view_alerts')
