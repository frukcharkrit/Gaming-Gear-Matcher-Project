# APP01/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import User, Role, ProPlayer, GamingGear, Preset, AIModel, Alert, Rating

# --- Custom Registration Form ---
class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=100, help_text='')

    class Meta:
        model = User
        # แก้ไขตรงนี้: เพิ่ม 'password' และ 'password2'
        fields = ('username', 'email', 'password', 'password2') 
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # กำหนด Role เป็น Member โดยอัตโนมัติ
        member_role, created = Role.objects.get_or_create(role_name='Member')
        user.role = member_role
        if commit:
            user.save()
        return user
    
# --- ProPlayer Form ---
class ProPlayerForm(forms.ModelForm):
    class Meta:
        model = ProPlayer
        fields = ['name', 'game', 'image_url', 'physique_vector'] # physique_vector อาจจะเป็น read-only หรือจัดการผ่าน AI backend
        widgets = {
            'physique_vector': forms.Textarea(attrs={'rows': 3, 'readonly': 'readonly'}), # อาจจะให้เป็น read-only
        }
        labels = {
            'name': 'ชื่อโปรเพลเยอร์',
            'game': 'ชื่อเกม',
            'image_url': 'URL รูปภาพ',
            'physique_vector': 'ข้อมูลสรีระ (AI Vector)',
        }

# --- GamingGear Form ---
class GamingGearForm(forms.ModelForm):
    class Meta:
        model = GamingGear
        fields = ['name', 'type', 'brand', 'specs', 'price', 'store_url', 'image_url']
        labels = {
            'name': 'ชื่ออุปกรณ์',
            'type': 'ประเภท',
            'brand': 'แบรนด์',
            'specs': 'สเปค (JSON)',
            'price': 'ราคา',
            'store_url': 'ลิงก์ร้านค้า',
            'image_url': 'URL รูปภาพ',
        }
        widgets = {
            'specs': forms.Textarea(attrs={'rows': 4}), # ให้พื้นที่ใหญ่ขึ้นสำหรับ JSON
        }

# --- Preset Form ---
class PresetForm(forms.ModelForm):
    class Meta:
        model = Preset
        fields = ['name']
        labels = {
            'name': 'ชื่อ Preset',
        }

# --- AIModel Form ---
class AIModelForm(forms.ModelForm):
    # อาจจะเพิ่ม ImageField สำหรับอัปโหลดไฟล์โมเดลจริง ถ้าเก็บในระบบไฟล์
    # file_path อาจจะเป็น CharField เก็บชื่อไฟล์ หรือ FileField
    class Meta:
        model = AIModel
        fields = ['name', 'version', 'file_path', 'is_active']
        labels = {
            'name': 'ชื่อโมเดล AI',
            'version': 'เวอร์ชัน',
            'file_path': 'ตำแหน่งไฟล์โมเดล',
            'is_active': 'ใช้งานอยู่',
        }

# --- Rating Form (สำหรับให้คะแนนจาก Member) ---
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['feedback_score', 'comment']
        labels = {
            'feedback_score': 'คะแนนการจับคู่',
            'comment': 'ความคิดเห็นเพิ่มเติม',
        }
        widgets = {
            'feedback_score': forms.RadioSelect(choices=Rating.feedback_score.field.choices),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

# --- Alert Form (อาจไม่จำเป็นต้องมีฟอร์มถ้าสร้างจาก backend เท่านั้น) ---
# class AlertForm(forms.ModelForm):
#     class Meta:
#         model = Alert
#         fields = '__all__' # หรือเลือกบางฟิลด์