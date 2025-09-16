# APP01/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.files.storage import FileSystemStorage # สำหรับอัปโหลดไฟล์
from django.conf import settings # สำหรับเข้าถึง MEDIA_ROOT

from .models import User, Role, ProPlayer, GamingGear, Preset, Rating, AIModel, Alert # นำเข้า Models ของคุณ
from .forms import RegisterForm, ProPlayerForm, GamingGearForm, PresetForm, AIModelForm # ต้องสร้าง Forms เหล่านี้ใน forms.py

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
def is_admin(user):
    return user.is_authenticated and user.role.role_name == 'Admin'

# Helper function เพื่อตรวจสอบว่าผู้ใช้เป็น Member
def is_member(user):
    return user.is_authenticated and user.role.role_name == 'Member'

def home_guest(request):
    # อาจจะแสดง Pro Players แนะนำ หรือ Gears ยอดนิยม
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
            # สมมติว่า RegisterForm จะสร้าง User และตั้งค่า role_id เป็น Member
            user = form.save()
            # ส่งอีเมลยืนยัน หรือเข้าสู่ระบบอัตโนมัติ
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'APP01/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                if user.role.role_name == 'Admin':
                    return redirect('admin_dashboard')
                else: # Member หรือ Guest ที่เพิ่งสมัคร
                    return redirect('home_member') # หรือ home_guest
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
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

        # Process image with AI
        # สมมติว่า AI_MODEL มีฟังก์ชัน process_image ที่รับ path รูปภาพแล้วคืนค่า physique_vector
        try:
            image_path = os.path.join(settings.MEDIA_ROOT, filename)
            # ตัวอย่างการประมวลผลรูปภาพ (ต้องมี AI_MODEL โหลดอยู่)
            # if AI_MODEL:
            #     # Load image using OpenCV
            #     img = cv2.imread(image_path)
            #     if img is None:
            #         messages.error(request, "Failed to load image for AI processing.")
            #         return redirect('upload_image')
            #     # Preprocess image (resize, normalize etc.)
            #     processed_img = cv2.resize(img, (224, 224)) # ตัวอย่าง
            #     processed_img = np.expand_dims(processed_img, axis=0)
            #     # Get physique vector from AI model
            #     user_physique_vector = AI_MODEL.predict(processed_img).tolist() # แปลงเป็น list เพื่อเก็บใน JSON/Text
            # else:
            #     messages.warning(request, "AI model not loaded. Using dummy data for matching.")
            #     user_physique_vector = [0.1, 0.2, 0.3] # Dummy vector


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
                # Store match history (Optional, if you want to log every match)
                # You might need to add a MatchHistory model if it's not in your ERD
                # For now, just pass data to result page
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

import json # สำหรับการแปลง JSON

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
    rating_form_needed = request.user.is_authenticated and request.user.role.role_name == 'Member'
    
    context = {
        'uploaded_image_url': match_result['uploaded_image_url'],
        'matched_player': matched_player,
        'pro_player_gears': pro_player_gears, # ชุดอุปกรณ์แนะนำของ Pro Player
        'temp_preset_gears': temp_preset_gears, # ชุดอุปกรณ์ที่ผู้ใช้กำลังแก้ไข
        'is_member': request.user.is_authenticated and request.user.role.role_name == 'Member',
        'rating_form_needed': rating_form_needed,
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
    # แสดงข้อมูลเฉพาะสมาชิก เช่น Presets ล่าสุด
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
                # share_link จะถูกสร้างเมื่อมีการแชร์จริงๆ หรือสร้างเป็น UUID ตอนนี้เลย
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
def rate_match(request):
    match_result = request.session.get('match_result')
    if not match_result:
        messages.error(request, 'No match result to rate.')
        return redirect('upload_image')

    matched_player = get_object_or_404(ProPlayer, player_id=match_result['matched_player_id'])

    if request.method == 'POST':
        feedback_score = request.POST.get('feedback_score') # 'Good', 'Neutral', 'Bad'
        comment = request.POST.get('comment', '')

        if feedback_score in ['Good', 'Neutral', 'Bad']:
            # ตรวจสอบว่าเคยให้คะแนน match นี้แล้วหรือยัง (อาจจะใช้ match_id ในอนาคต)
            # สำหรับตอนนี้ อาจจะให้คะแนนได้เรื่อยๆ หรือมี logic ตรวจสอบเพิ่มเติม
            Rating.objects.create(
                user=request.user,
                proplayer=matched_player,
                feedback_score=feedback_score,
                comment=comment,
            )
            messages.success(request, 'Thank you for your feedback!')
            # เคลียร์ session หรือ redirect ไปหน้าอื่น
            if 'match_result' in request.session:
                del request.session['match_result']
            return redirect('home_member')
        else:
            messages.error(request, 'Invalid feedback score provided.')
    
    # ถ้าเข้ามาหน้านี้แบบ GET ให้แสดงฟอร์มให้คะแนน
    context = {
        'matched_player': matched_player,
        'uploaded_image_url': match_result.get('uploaded_image_url'),
    }
    return render(request, 'APP01/rate_match.html', context)

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
        form = PresetForm(request.POST, instance=preset)
        if form.is_valid():
            form.save() # อัปเดตชื่อ Preset
            
            # การจัดการ Gears (ซับซ้อนขึ้น อาจใช้ FormSet หรือจัดการด้วย JS/AJAX)
            # ตัวอย่าง: ลบของเก่าออกแล้วเพิ่มของใหม่เข้าไป
            PresetGear.objects.filter(preset=preset).delete()
            selected_gear_ids = request.POST.getlist('selected_gears') # สมมติว่ามี input field ชื่อ selected_gears
            for order, gear_id in enumerate(selected_gear_ids):
                gear = get_object_or_404(GamingGear, gear_id=gear_id)
                PresetGear.objects.create(preset=preset, gear=gear, order=order + 1)
            
            messages.success(request, f'Preset "{preset.name}" updated successfully!')
            return redirect('preset_detail', preset_id=preset.preset_id)
        else:
            messages.error(request, 'Failed to update preset.')
    else:
        form = PresetForm(instance=preset)
    
    available_gears = GamingGear.objects.all() # สำหรับเลือกเพิ่ม
    context = {
        'form': form,
        'preset': preset,
        'current_gears': current_gears,
        'available_gears': available_gears,
    }
    return render(request, 'APP01/edit_preset.html', context)

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def delete_preset(request, preset_id):
    preset = get_object_or_404(Preset, preset_id=preset_id, user=request.user)
    if request.method == 'POST':
        preset.delete()
        messages.success(request, f'Preset "{preset.name}" deleted successfully.')
        return redirect('manage_presets')
    return render(request, 'APP01/confirm_delete_preset.html', {'preset': preset}) # อาจทำเป็น modal

@login_required(login_url='login')
@user_passes_test(is_member, login_url='home_guest')
def share_preset(request, preset_id):
    preset = get_object_or_404(Preset, preset_id=preset_id, user=request.user)
    if not preset.share_link:
        # สร้างลิงก์แชร์ที่ไม่ซ้ำกัน
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

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def admin_dashboard(request):
    # สถิติภาพรวม
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

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def admin_manage_gears(request): # นี่คือฟังก์ชันที่หายไป
    gears = GamingGear.objects.all().order_by('name')
    context = {'gears': gears}
    return render(request, 'APP01/admin_manage_gears.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def admin_add_gear(request): # นี่คือฟังก์ชันที่หายไป
    if request.method == 'POST':
        form = GamingGearForm(request.POST, request.FILES)
        if form.is_valid():
            new_gear = form.save()
            messages.success(request, f'Gear "{new_gear.name}" added successfully!')
            return redirect('admin_manage_gears')
        else:
            messages.error(request, 'Failed to add gear. Please correct the errors.')
    else:
        form = GamingGearForm()
    return render(request, 'APP01/admin_add_gear.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def admin_edit_gear(request, gear_id): # นี่คือฟังก์ชันที่หายไป
    gear = get_object_or_404(GamingGear, gear_id=gear_id)
    if request.method == 'POST':
        form = GamingGearForm(request.POST, request.FILES, instance=gear)
        if form.is_valid():
            form.save()
            messages.success(request, f'Gear "{gear.name}" updated successfully!')
            return redirect('admin_manage_gears')
        else:
            messages.error(request, 'Failed to update gear. Please correct the errors.')
    else:
        form = GamingGearForm(instance=gear)
    return render(request, 'APP01/admin_edit_gear.html', {'form': form, 'gear': gear})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def admin_delete_gear(request, gear_id): # นี่คือฟังก์ชันที่หายไป
    gear = get_object_or_404(GamingGear, gear_id=gear_id)
    if request.method == 'POST':
        name = gear.name
        gear.delete()
        messages.success(request, f'Gear "{name}" deleted successfully.')
        return redirect('admin_manage_gears')
    return render(request, 'APP01/admin_confirm_delete_gear.html', {'gear': gear})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def manage_members(request):
    members = User.objects.filter(role__role_name='Member').order_by('username')
    context = {'members': members}
    return render(request, 'APP01/admin_members.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def edit_member(request, user_id):
    member = get_object_or_404(User, user_id=user_id)
    # ฟอร์มสำหรับแก้ไขข้อมูลสมาชิก เช่น บทบาท, สถานะ
    # ต้องสร้าง MemberEditForm ใน forms.py
    # if request.method == 'POST':
    #     form = MemberEditForm(request.POST, instance=member)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, 'Member updated successfully.')
    #         return redirect('manage_members')
    # else:
    #     form = MemberEditForm(instance=member)
    # context = {'form': form, 'member': member}
    # return render(request, 'APP01/admin_edit_member.html', context)
    messages.info(request, f"Editing user: {member.username} - functionality to be implemented.")
    return redirect('manage_members')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def delete_member(request, user_id):
    member = get_object_or_404(User, user_id=user_id)
    if request.method == 'POST':
        username = member.username
        member.delete()
        messages.success(request, f'Member {username} deleted successfully.')
        return redirect('manage_members')
    return render(request, 'APP01/admin_confirm_delete_member.html', {'member': member})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def manage_pro_players(request): # S_Pro_List
    pro_players = ProPlayer.objects.all().order_by('name')
    context = {'pro_players': pro_players}
    return render(request, 'APP01/admin_pro_players.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def add_pro_player(request): # S_Add_Pro_Player
    if request.method == 'POST':
        form = ProPlayerForm(request.POST, request.FILES) # request.FILES ถ้ามีการอัปโหลดรูปภาพ
        if form.is_valid():
            new_player = form.save()
            # สมมติว่า physique_vector จะถูกคำนวณหรือใส่ทีหลัง
            messages.success(request, f'Pro Player "{new_player.name}" added successfully!')
            return redirect('manage_pro_players')
        else:
            messages.error(request, 'Failed to add Pro Player. Please correct the errors.')
    else:
        form = ProPlayerForm()
    return render(request, 'APP01/admin_add_pro_player.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def edit_pro_player(request, player_id): # S_Edit_Pro_Player
    pro_player = get_object_or_404(ProPlayer, player_id=player_id)
    
    if request.method == 'POST':
        form = ProPlayerForm(request.POST, request.FILES, instance=pro_player)
        if form.is_valid():
            form.save()
            # อาจมี logic สำหรับอัปเดต physique_vector ถ้ามีการอัปโหลดรูปใหม่
            messages.success(request, f'Pro Player "{pro_player.name}" updated successfully!')
            return redirect('manage_pro_players')
        else:
            messages.error(request, 'Failed to update Pro Player. Please correct the errors.')
    else:
        form = ProPlayerForm(instance=pro_player)
    
    # ดึง Gears ที่ Pro Player คนนี้ใช้
    current_gears = GamingGear.objects.filter(proplayergear__player=pro_player)
    # Gears ทั้งหมดสำหรับเลือก
    all_gears = GamingGear.objects.all()

    context = {
        'form': form,
        'pro_player': pro_player,
        'current_gears': current_gears,
        'all_gears': all_gears,
    }
    return render(request, 'APP01/admin_edit_pro_player.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def delete_pro_player(request, player_id): # ทำงานจาก S_Edit_Pro_Player
    pro_player = get_object_or_404(ProPlayer, player_id=player_id)
    if request.method == 'POST':
        name = pro_player.name
        pro_player.delete()
        messages.success(request, f'Pro Player "{name}" deleted successfully.')
        return redirect('manage_pro_players')
    return render(request, 'APP01/admin_confirm_delete_pro_player.html', {'pro_player': pro_player})


# จัดการ Gears ภายใน Pro Player (Manage Gears)
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def manage_pro_player_gears(request, player_id): # S_Admin_Gears
    pro_player = get_object_or_404(ProPlayer, player_id=player_id)
    
    if request.method == 'POST':
        # Logic สำหรับการเพิ่ม/ลบ Gear ของ Pro Player นี้
        selected_gear_ids = request.POST.getlist('selected_gears') # IDs ที่ถูกเลือกจากหน้าจอ
        
        # ลบ Gear ที่เคยเชื่อมทั้งหมด
        ProPlayerGear.objects.filter(player=pro_player).delete()
        
        # เพิ่ม Gear ที่เลือกใหม่
        for gear_id in selected_gear_ids:
            gear = get_object_or_404(GamingGear, gear_id=gear_id)
            ProPlayerGear.objects.create(player=pro_player, gear=gear)
        
        messages.success(request, f'Gears for {pro_player.name} updated successfully!')
        return redirect('edit_pro_player', player_id=player_id) # กลับไปหน้าแก้ไข Pro Player
    
    current_gears = GamingGear.objects.filter(proplayergear__player=pro_player).values_list('gear_id', flat=True)
    all_gears = GamingGear.objects.all().order_by('name')
    
    context = {
        'pro_player': pro_player,
        'current_gears': list(current_gears), # แปลงเป็น list สำหรับ template
        'all_gears': all_gears,
    }
    return render(request, 'APP01/admin_manage_pro_player_gears.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def manage_ai_models(request):
    models = AIModel.objects.all().order_by('-created_at')
    context = {'models': models}
    return render(request, 'APP01/admin_ai_models.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def add_ai_model(request):
    if request.method == 'POST':
        form = AIModelForm(request.POST, request.FILES)
        if form.is_valid():
            new_model = form.save(commit=False)
            new_model.created_at = timezone.now() # Django timezone import needed
            new_model.last_trained_at = timezone.now()
            new_model.is_active = False # Default to inactive, admin sets active later
            new_model.save()
            messages.success(request, f'AI Model "{new_model.name}" added successfully.')
            return redirect('manage_ai_models')
        else:
            messages.error(request, 'Failed to add AI Model.')
    else:
        form = AIModelForm()
    return render(request, 'APP01/admin_add_ai_model.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def edit_ai_model(request, model_id):
    ai_model = get_object_or_404(AIModel, model_id=model_id)
    if request.method == 'POST':
        form = AIModelForm(request.POST, request.FILES, instance=ai_model)
        if form.is_valid():
            form.save()
            messages.success(request, f'AI Model "{ai_model.name}" updated successfully.')
            return redirect('manage_ai_models')
        else:
            messages.error(request, 'Failed to update AI Model.')
    else:
        form = AIModelForm(instance=ai_model)
    return render(request, 'APP01/admin_edit_ai_model.html', {'form': form, 'ai_model': ai_model})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def delete_ai_model(request, model_id):
    ai_model = get_object_or_404(AIModel, model_id=model_id)
    if request.method == 'POST':
        name = ai_model.name
        ai_model.delete()
        messages.success(request, f'AI Model "{name}" deleted successfully.')
        return redirect('manage_ai_models')
    return render(request, 'APP01/admin_confirm_delete_ai_model.html', {'ai_model': ai_model})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home_guest')
def set_active_ai_model(request, model_id):
    if request.method == 'POST':
        AIModel.objects.update(is_active=False) # Set all to inactive
        model_to_activate = get_object_or_404(AIModel, model_id=model_id)
        model_to_activate.is_active = True
        model_to_activate.save()
        messages.success(request, f'AI Model "{model_to_activate.name}" is now active.')
    return redirect('manage_ai_models')

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

