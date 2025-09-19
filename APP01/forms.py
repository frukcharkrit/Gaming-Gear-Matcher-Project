# APP01/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import User, Role, ProPlayer, GamingGear, Preset, AIModel, Alert, Rating, ProPlayerGear # เพิ่ม ProPlayerGear

# --- Custom Login Form ---
class LoginForm(AuthenticationForm):
    # ไม่จำเป็นต้องเพิ่ม field ใหม่, AuthenticationForm มี username และ password อยู่แล้ว
    pass

# --- Custom Registration Form ---
class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=100, help_text='')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2') 
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        member_role, created = Role.objects.get_or_create(role_name='Member')
        user.role = member_role
        if commit:
            user.save()
        return user

# --- ProPlayer Form (ปรับปรุง) ---
class ProPlayerForm(forms.ModelForm):
    # เปลี่ยนจาก ModelMultipleChoiceField เป็น CharField เพื่อให้กรอกข้อความเองได้
    gears_text = forms.CharField(
        label='อุปกรณ์ Gaming Gear ที่ใช้',
        required=False,
        help_text='กรอกชื่ออุปกรณ์หลายชิ้นโดยคั่นด้วยเครื่องหมายจุลภาค (,)',
        widget=forms.TextInput(attrs={'placeholder': 'เช่น Mouse, Keyboard, Headset', 'class': 'form-control'})
    )

    class Meta:
        model = ProPlayer
        # เปลี่ยน 'gears' เป็น 'gears_text'
        fields = ['name', 'game', 'image_url', 'gears_text']
        labels = {
            'name': 'ชื่อโปรเพลเยอร์',
            'game': 'เกมที่เล่น',
            'image_url': 'URL รูปภาพโปรไฟล์',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'เช่น s1mple', 'class': 'form-control'}),
            'game': forms.TextInput(attrs={'placeholder': 'เช่น Counter-Strike', 'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'เช่น http://example.com/s1mple.jpg', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ตั้งค่าคลาส 'form-control' ให้กับฟิลด์ที่ไม่ได้ใช้ widgets ใน Meta
        self.fields['gears_text'].widget.attrs['class'] = 'form-control'
        
        if self.instance and self.instance.pk:
            # สำหรับการแก้ไข: ดึงชื่อ Gears ที่ใช้อยู่มาแสดงผลในช่องข้อความ
            gear_names = self.instance.proplayergear_set.values_list('gear__name', flat=True)
            self.fields['gears_text'].initial = ', '.join(gear_names)
        
        # ลบฟิลด์ที่ไม่ต้องการให้แก้ไข
        if 'physique_vector' in self.fields:
            del self.fields['physique_vector']

    def save(self, commit=True):
        player = super().save(commit=False)
        if commit:
            player.save()
            
            # จัดการ Many-to-Many Relationship (ProPlayerGear)
            if 'gears_text' in self.cleaned_data:
                # แยกข้อความที่กรอกด้วยเครื่องหมายจุลภาคและลบช่องว่าง
                gear_list = [name.strip() for name in self.cleaned_data['gears_text'].split(',') if name.strip()]
                
                # ลบ Gear เก่าทั้งหมดของ Pro Player นี้ก่อน
                ProPlayerGear.objects.filter(player=player).delete()
                
                # เพิ่ม Gear ใหม่หรือใช้ที่มีอยู่แล้ว
                for gear_name in gear_list:
                    gear, created = GamingGear.objects.get_or_create(name=gear_name)
                    ProPlayerGear.objects.create(player=player, gear=gear)

        return player
    
# --- GamingGear Form (ปรับปรุง) ---
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
            'name': forms.TextInput(attrs={'placeholder': 'เช่น Razer DeathAdder V3 Pro', 'class': 'form-control'}),
            'type': forms.TextInput(attrs={'placeholder': 'เช่น Mouse, Keyboard, Headset', 'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'placeholder': 'เช่น Razer', 'class': 'form-control'}),
            'specs': forms.Textarea(attrs={'placeholder': '{"sensor": "Optical", "dpi": "30000"}', 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'placeholder': 'เช่น 5000', 'class': 'form-control'}),
            'store_url': forms.URLInput(attrs={'placeholder': 'เช่น http://store.com/item', 'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'เช่น http://example.com/gear.jpg', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure 'form-control' class is added to all fields for consistent styling
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = 'form-control'

# ... (ฟอร์มอื่นๆ) ...

class PresetForm(forms.ModelForm):
    class Meta:
        model = Preset
        fields = ['name']
        labels = {
            'name': 'ชื่อ Preset',
        }

class AIModelForm(forms.ModelForm):
    class Meta:
        model = AIModel
        fields = ['name', 'version', 'file_path', 'is_active']
        labels = {
            'name': 'ชื่อโมเดล AI',
            'version': 'เวอร์ชัน',
            'file_path': 'ตำแหน่งไฟล์โมเดล',
            'is_active': 'ใช้งานอยู่',
        }

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