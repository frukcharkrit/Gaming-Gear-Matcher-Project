# Gaming Gear Matcher — Use Case Catalog

> **Actors:** Guest · Member · Admin
> **Last updated:** 2026-02-23

---

## สารบัญ

- [UC-G: Guest Use Cases](#uc-g-guest-use-cases)
- [UC-M: Member Use Cases](#uc-m-member-use-cases)
- [UC-A: Admin Use Cases](#uc-a-admin-use-cases)

---

## UC-G: Guest Use Cases

---

### UC-G01 — ดูหน้าแรก (Home Guest)

| Field | Detail |
|---|---|
| **Actor** | Guest |
| **Route** | `GET /` |
| **View** | `home_guest` |
| **Precondition** | - |
| **Main Flow** | 1. Guest เปิดเว็บไซต์ <br>2. ระบบแสดง Pro Player แนะนำ (5 คนแรก) และ Gear แนะนำ (5 ชิ้นแรก) |
| **Postcondition** | แสดงหน้าแรกพร้อม featured content |

---

### UC-G02 — สมัครสมาชิก (Register)

| Field | Detail |
|---|---|
| **Actor** | Guest |
| **Route** | `GET/POST /register/` |
| **View** | `register` |
| **Precondition** | Guest ยังไม่มีบัญชี |
| **Main Flow** | 1. Guest กรอก username, email, password <br>2. ระบบ validate ด้วย `RegisterForm` <br>3. ระบบสร้าง User ใหม่ กำหนด Role = `Member` อัตโนมัติ <br>4. Redirect ไปหน้า Login |
| **Alternative Flow** | 2a. ข้อมูลไม่ผ่าน validation → แสดง error message |
| **Postcondition** | User ใหม่ถูกสร้างใน DB พร้อม Role = Member |

---

### UC-G03 — เข้าสู่ระบบ (Login)

| Field | Detail |
|---|---|
| **Actor** | Guest |
| **Route** | `GET/POST /login/` |
| **View** | `user_login` |
| **Precondition** | Guest มีบัญชีอยู่แล้ว |
| **Main Flow** | 1. Guest กรอก username/password <br>2. ระบบ authenticate ด้วย `LoginForm` <br>3. ถ้าเป็น Admin → redirect `/admin-dashboard/` <br>4. ถ้าเป็น Member → redirect `/member/home/` |
| **Alternative Flow** | 2a. บัญชีถูกแบน (`is_active=False`) → แสดงวันที่ถูกแบน <br>2b. username/password ผิด → แสดง error |
| **Postcondition** | Session ถูกสร้าง, User เข้าสู่ระบบแล้ว |

---

### UC-G04 — ออกจากระบบ (Logout)

| Field | Detail |
|---|---|
| **Actor** | Guest / Member / Admin |
| **Route** | `GET /logout/` |
| **View** | `user_logout` |
| **Precondition** | User Login อยู่ |
| **Main Flow** | 1. User คลิก Logout <br>2. ระบบล้าง Session <br>3. Redirect ไปหน้าแรก `/` |
| **Postcondition** | Session ถูกล้าง |

---

### UC-G05 — ขอรีเซ็ตรหัสผ่าน (Forgot Password)

| Field | Detail |
|---|---|
| **Actor** | Guest |
| **Route** | `GET/POST /forgot-password/` |
| **View** | `forgot_password` |
| **Precondition** | Guest จำรหัสผ่านไม่ได้ |
| **Main Flow** | 1. Guest กรอก Email <br>2. ระบบสร้าง `PasswordResetRequest` (status=Pending) <br>3. แสดง success message และรอ Admin อนุมัติ |
| **Alternative Flow** | 2a. Email ไม่พบในระบบ → แสดง success เหมือนเดิม (security) <br>2b. มี Request ที่ Pending อยู่แล้ว → แจ้งเตือน |
| **Postcondition** | `PasswordResetRequest` ถูกสร้างใน DB |

---

### UC-G06 — ทำ Wizard จับคู่ Gear (Gear Matching Wizard)

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /start-matching/` → `/wizard/quiz/` → `POST /wizard/process-quiz/` |
| **View** | `start_matching`, `wizard_quiz`, `process_quiz` |
| **Precondition** | - |
| **Main Flow** | 1. Guest คลิก "Start Matching" → หน้า Wizard Start <br>2. ตอบแบบสอบถาม 3 ข้อ: genre, hand_size, grip <br>3. POST ส่ง quiz → ระบบรัน `HybridRecommender.recommend_variant_setups()` <br>4. บันทึกผลลัพธ์ใน Session <br>5. Redirect ไปหน้า Matching Result |
| **Alternative Flow** | 3a. ไม่พบ Gear ที่เหมาะสม → redirect กลับหน้า Quiz พร้อม error |
| **Postcondition** | Session มีข้อมูล 3 Variant (Performance, Balanced, Pro Choice) |

---

### UC-G07 — ดูผลการจับคู่ Gear (Matching Result)

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /matching-result/` |
| **View** | `matching_result` |
| **Precondition** | Session มี `wizard_preset` |
| **Main Flow** | 1. ระบบดึง Gear ที่เลือกจาก Session <br>2. เรียก `AssociationRuleMiner` เพื่อหา Gear แนะนำเพิ่มเติม <br>3. แสดง 3 Variant tabs (Performance / Balanced / Pro Choice) <br>4. แสดง "My Setup" และ Association-based recommendations |
| **Postcondition** | ผู้ใช้เห็นผลการแนะนำ Gear |

---

### UC-G08 — เลือก Gear ใน Wizard (Wizard Select Gear)

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /wizard/select/<category>/` |
| **View** | `wizard_select_gear` |
| **Precondition** | อยู่ใน Wizard flow |
| **Main Flow** | 1. ระบบแสดง Gear ตาม category ที่เลือก <br>2. ผู้ใช้ filter ตาม Brand หรือ sort ตาม Price/Pro Usage <br>3. ผู้ใช้ค้นหาด้วยชื่อหรือ Brand |
| **Postcondition** | ผู้ใช้เห็นรายการ Gear พร้อมตัวเลือก filter/sort |

---

### UC-G09 — เพิ่ม/ลบ Gear ใน Wizard Session

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /wizard/add/<gear_id>/`, `GET /wizard/remove/<gear_id>/` |
| **View** | `wizard_add_gear`, `wizard_remove_gear` |
| **Precondition** | อยู่ใน Wizard flow |
| **Main Flow** | 1. ผู้ใช้คลิก Add → Gear ถูกเพิ่มใน Session <br>2. ถ้า Category นั้นมี Gear อยู่แล้ว → แทนที่ (1 Gear ต่อ Category) <br>3. คลิก Remove → Gear ถูกลบออกจาก Session |
| **Postcondition** | `wizard_preset` ใน Session อัปเดต |

---

### UC-G10 — ดูรายละเอียด Gear

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /gear/<gear_id>/` |
| **View** | `gear_detail` |
| **Precondition** | - |
| **Main Flow** | 1. ระบบแสดง specs ทั้งหมดของ Gear (จาก JSONField) <br>2. แสดง Pro Players ที่ใช้ Gear นี้ <br>3. แสดง Related Gears ในประเภทเดียวกัน <br>4. Member เห็นปุ่ม Add to Wizard |
| **Alternative Flow** | 1a. ไม่พบใน DB → แสดงข้อมูล Demo แทน |
| **Postcondition** | ผู้ใช้เห็นข้อมูล Gear ครบถ้วน |

---

### UC-G11 — ดูรายละเอียด Pro Player

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /pro-player/<player_id>/` |
| **View** | `pro_player_detail` |
| **Precondition** | - |
| **Main Flow** | 1. ระบบแสดงข้อมูล Pro Player: ชื่อ, เกม, bio, settings, eDPI <br>2. แสดง Gear ทั้งหมดที่ Pro Player ใช้ |
| **Alternative Flow** | 1a. ไม่พบใน DB → แสดง Demo Player แทน |
| **Postcondition** | ผู้ใช้เห็น setup ของ Pro Player |

---

### UC-G12 — ค้นหาทั่วไป (Global Search)

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /search/` |
| **View** | `global_search` |
| **Precondition** | - |
| **Main Flow** | 1. ผู้ใช้พิมพ์คำค้นหา <br>2. ระบบค้นหาทั้ง Gear และ Pro Player พร้อมกัน <br>3. แสดงผลลัพธ์รวม |
| **Postcondition** | แสดงผลการค้นหา |

---

### UC-G13 — ค้นหา Gear / Pro Player แยกหมวด

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /search/gear/`, `GET /search/pro-player/` |
| **View** | `search_gear`, `search_pro_player` |
| **Precondition** | - |
| **Main Flow** | 1. ผู้ใช้ค้นหา Gear หรือ Pro Player ตาม category ที่ต้องการ |
| **Postcondition** | แสดงผลการค้นหาแบบเจาะจง |

---

### UC-G14 — ดู Preset ที่แชร์ (Shared Preset)

| Field | Detail |
|---|---|
| **Actor** | Guest / Member |
| **Route** | `GET /share/<share_link>/` |
| **View** | `view_shared_preset` |
| **Precondition** | มี share_link ที่ถูกต้อง |
| **Main Flow** | 1. ผู้ใช้เปิด link ที่ได้รับมา <br>2. ระบบหา Preset จาก UUID share_link <br>3. แสดง Gear ทั้งหมดใน Preset |
| **Alternative Flow** | 2a. ไม่พบ Preset → 404 |
| **Postcondition** | ผู้ใช้เห็น Preset ของคนอื่น |

---

## UC-M: Member Use Cases

> ทุก Use Case ในกลุ่มนี้ต้องการ `@login_required` และ role = Member

---

### UC-M01 — ดูหน้าหลัก Member

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /member/home/` |
| **View** | `home_member` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. ระบบแสดง Preset ของตัวเอง, Pro Player แนะนำ, Gear ใหม่ |
| **Postcondition** | Member เห็นหน้า Dashboard |

---

### UC-M02 — ดูโปรไฟล์

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /profile/` |
| **View** | `user_profile` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. ระบบแสดงข้อมูล: username, email, รูปโปรไฟล์, Preset ทั้งหมดของตัวเอง |
| **Postcondition** | Member เห็นโปรไฟล์ตัวเอง |

---

### UC-M03 — แก้ไขโปรไฟล์

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET/POST /profile/edit/` |
| **View** | `edit_profile` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. Member แก้ไข username, email, รูปโปรไฟล์ <br>2. ระบบ validate และบันทึก |
| **Postcondition** | ข้อมูลโปรไฟล์อัปเดตใน DB |

---

### UC-M04 — เปลี่ยนรหัสผ่าน

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET/POST /profile/change-password/` |
| **View** | `change_password` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. Member กรอก รหัสผ่านเดิม และรหัสผ่านใหม่ 2 ครั้ง <br>2. ระบบ validate และอัปเดต password |
| **Alternative Flow** | 2a. รหัสผ่านเดิมผิด → แสดง error |
| **Postcondition** | Password อัปเดตใน DB |

---

### UC-M05 — บันทึก Preset

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET/POST /preset/save/` |
| **View** | `save_preset` |
| **Precondition** | Login แล้ว, มี `wizard_preset` ใน Session |
| **Main Flow** | 1. Member ตั้งชื่อ Preset <br>2. ระบบสร้าง `Preset` object พร้อม `PresetGear` สำหรับทุก Gear <br>3. สร้าง `share_link` (UUID) อัตโนมัติ |
| **Postcondition** | Preset บันทึกใน DB |

---

### UC-M06 — ดูรายการ Preset ของตัวเอง

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /presets/` |
| **View** | `manage_presets` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. ระบบแสดง Preset ทั้งหมดของ Member พร้อมรูป Gear แต่ละชิ้น |
| **Postcondition** | Member เห็น Preset ทั้งหมด |

---

### UC-M07 — ดูรายละเอียด Preset

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /preset/<preset_id>/` |
| **View** | `preset_detail` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. ระบบแสดง Gear ทั้งหมดใน Preset, คะแนน Rating, share link |
| **Postcondition** | Member เห็นรายละเอียด Preset |

---

### UC-M08 — แก้ไข Gear ใน Preset

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET/POST /preset/<preset_id>/edit/` |
| **View** | `edit_preset` |
| **Precondition** | Login แล้ว, เป็นเจ้าของ Preset |
| **Main Flow** | 1. Member เพิ่ม/ลบ Gear ใน Preset <br>2. ระบบ update `PresetGear` |
| **Postcondition** | Preset อัปเดตใน DB |

---

### UC-M09 — เปลี่ยนชื่อ Preset

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `POST /preset/<preset_id>/edit-name/` |
| **View** | `edit_preset_name` |
| **Precondition** | Login แล้ว, เป็นเจ้าของ Preset |
| **Main Flow** | 1. Member ส่งชื่อใหม่ <br>2. ระบบอัปเดต `Preset.name` |
| **Postcondition** | ชื่อ Preset อัปเดต |

---

### UC-M10 — ลบ Preset

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `POST /preset/<preset_id>/delete/` |
| **View** | `delete_preset` |
| **Precondition** | Login แล้ว, เป็นเจ้าของ Preset |
| **Main Flow** | 1. Member ยืนยันการลบ <br>2. ระบบลบ Preset และ `PresetGear` ทั้งหมด (CASCADE) |
| **Postcondition** | Preset ถูกลบออกจาก DB |

---

### UC-M11 — ให้คะแนน Preset (Rating)

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `POST /preset/<preset_id>/rate/` |
| **View** | `submit_preset_rating` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. Member เลือกคะแนน 1–5 ดาว และ comment (ถ้ามี) <br>2. ระบบสร้างหรืออัปเดต `PresetRating` (unique per user+preset) |
| **Postcondition** | `PresetRating` บันทึกใน DB |

---

### UC-M12 — แชร์ Preset

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /preset/<preset_id>/share/` |
| **View** | `share_preset` |
| **Precondition** | Login แล้ว, เป็นเจ้าของ Preset |
| **Main Flow** | 1. ระบบแสดง share link (UUID) ของ Preset <br>2. Member คัดลอก link แชร์ให้คนอื่น |
| **Postcondition** | Member ได้ URL สำหรับแชร์ |

---

### UC-M13 — เปลี่ยน Gear ใน Preset (Replace)

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /preset/<preset_id>/replace-gear/<old_gear_id>/` <br>`GET /preset/<preset_id>/replace-gear/<old_gear_id>/with/<new_gear_id>/` |
| **View** | `replace_gear`, `confirm_replace` |
| **Precondition** | Login แล้ว, เป็นเจ้าของ Preset |
| **Main Flow** | 1. Member คลิก Replace บน Gear ที่ต้องการเปลี่ยน <br>2. ระบบแสดง Gear อื่นในประเภทเดียวกัน <br>3. Member เลือก Gear ใหม่ → ยืนยัน → ระบบแทนที่ใน `PresetGear` |
| **Postcondition** | Gear ใน Preset ถูกเปลี่ยน |

---

### UC-M14 — ใช้ Gear ทั้งหมดของ Pro Player

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /preset/use-all/<player_id>/` |
| **View** | `use_all_gears` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. Member คลิก "Use All" บนหน้า Pro Player <br>2. ระบบดึง Gear ทั้งหมดของ Pro Player ลง Session <br>3. Redirect ไปหน้า Save Preset |
| **Postcondition** | Session มี Gear ของ Pro Player พร้อม save |

---

### UC-M15 — ดู Notification / Messages

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /profile/messages/` |
| **View** | `user_messages` |
| **Precondition** | Login แล้ว |
| **Main Flow** | 1. ระบบแสดง Notification ทั้งหมดเรียงตาม `created_at` desc <br>2. Member อ่านข้อความ (เช่น ผล Password Reset) |
| **Postcondition** | Member เห็น Notification |

---

### UC-M16 — Mark Notification อ่านแล้ว

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `GET /message/read/<notification_id>/` |
| **View** | `mark_message_read` |
| **Precondition** | Login แล้ว, เป็นเจ้าของ Notification |
| **Main Flow** | 1. Member คลิกอ่าน <br>2. ระบบตั้ง `Notification.is_read = True` |
| **Postcondition** | Notification ถูก mark อ่านแล้ว |

---

### UC-M17 — ให้คะแนนผลการจับคู่ (Submit Rating)

| Field | Detail |
|---|---|
| **Actor** | Member |
| **Route** | `POST /matching-result/submit-rating/` |
| **View** | `submit_rating` |
| **Precondition** | Login แล้ว, อยู่ในหน้าผลการจับคู่ |
| **Main Flow** | 1. Member ให้คะแนน Matching Result <br>2. ระบบบันทึก Rating สำหรับ Preset นั้น |
| **Postcondition** | Rating บันทึกใน DB |

---

### UC-M18 — โหลด Variant Preset

| Field | Detail |
|---|---|
| **Actor** | Member / Guest |
| **Route** | `GET /wizard/load-preset/<variant_name>/` |
| **View** | `wizard_load_preset` |
| **Precondition** | Session มี variants_data |
| **Main Flow** | 1. ผู้ใช้คลิก tab Performance / Balanced / Pro Choice <br>2. ระบบโหลด Gear ของ Variant นั้นลง `wizard_preset` session <br>3. Redirect ไปหน้า Matching Result |
| **Postcondition** | Session อัปเดตเป็น Gear ของ Variant ที่เลือก |

---

## UC-A: Admin Use Cases

> ทุก Use Case ในกลุ่มนี้ต้องการ `@login_required` + `is_admin()` (is_superuser หรือ role = Admin)

---

### UC-A01 — ดู Admin Dashboard

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `GET /admin-dashboard/` |
| **View** | `admin_dashboard` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. ระบบแสดงสถิติ: จำนวน User, Gear, ProPlayer, Preset <br>2. แสดง Alert ที่ยังไม่ได้อ่าน <br>3. แสดง AdminLog ล่าสุด |
| **Postcondition** | Admin เห็นภาพรวมระบบ |

---

### UC-A02 — จัดการ User (ดู / แก้ไข / ลบ)

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `GET /admin-dashboard/users/` <br>`GET/POST /admin-dashboard/users/edit/<user_id>/` <br>`POST /admin-dashboard/users/delete/<user_id>/` |
| **View** | `admin_users`, `admin_edit_user`, `admin_delete_user` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. Admin ดูรายชื่อ User ทั้งหมด <br>2. คลิก Edit → แก้ไข username, email, role <br>3. คลิก Delete → ลบ User (ไม่สามารถลบตัวเองได้) |
| **Alternative Flow** | 3a. Admin ลบตัวเอง → แสดง error |
| **Postcondition** | User อัปเดต/ถูกลบใน DB |

---

### UC-A03 — แบน / ปลดแบน Member

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `POST /admin-dashboard/members/<user_id>/toggle-status/` |
| **View** | `admin_toggle_user_status` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. Admin คลิก Ban/Unban <br>2. ระบบ toggle `User.is_active` <br>3. ถ้า Ban → บันทึก `banned_at` timestamp และสร้าง `AdminLog` <br>4. `BannedUserMiddleware` จะ kick user ออกใน request ถัดไป |
| **Postcondition** | `User.is_active` เปลี่ยน, `AdminLog` บันทึก |

---

### UC-A04 — จัดการ Pro Player (CRUD)

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `GET /admin-dashboard/pro-players/` <br>`GET/POST /admin-dashboard/pro-players/add/` <br>`GET/POST /admin-dashboard/pro-players/<id>/edit/` <br>`POST /admin-dashboard/pro-players/<id>/delete/` |
| **View** | `admin_pro_players`, `admin_add_pro_player`, `admin_edit_pro_player`, `admin_delete_pro_player` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. Admin ดูรายชื่อ Pro Player ทั้งหมด <br>2. เพิ่ม Pro Player ใหม่ (ชื่อ, เกม, bio, settings, eDPI, รูปภาพ) <br>3. แก้ไข หรือ ลบ Pro Player <br>4. ระบบสร้าง `AdminLog` ทุกครั้ง |
| **Postcondition** | Pro Player CRUD ใน DB + AdminLog |

---

### UC-A05 — จัดการ Gaming Gear (CRUD)

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `GET /admin-dashboard/gears/` <br>`GET/POST /admin-dashboard/gears/add/` <br>`GET/POST /admin-dashboard/gears/<id>/edit/` <br>`POST /admin-dashboard/gears/<id>/delete/` |
| **View** | `admin_gears`, `admin_add_gear`, `admin_edit_gear`, `admin_delete_gear` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. Admin ดูรายการ Gear ทั้งหมด <br>2. เพิ่ม Gear ใหม่ (ชื่อ, ประเภท, brand, specs JSON, ราคา, รูปภาพ) <br>3. แก้ไข หรือ ลบ Gear <br>4. ระบบสร้าง `AdminLog` ทุกครั้ง |
| **Postcondition** | Gear CRUD ใน DB + AdminLog |

---

### UC-A06 — อนุมัติ/ปฏิเสธคำขอรีเซ็ตรหัสผ่าน

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `GET /admin-dashboard/password-requests/` <br>`POST /admin-dashboard/password-requests/<id>/approve/` |
| **View** | `admin_password_requests`, `approve_password_request` |
| **Precondition** | Login เป็น Admin, มี `PasswordResetRequest` (status=Pending) |
| **Main Flow (Approve)** | 1. Admin คลิก Approve <br>2. ระบบ generate random password (10 chars) <br>3. `user.set_password(new_password)` <br>4. สร้าง `Notification` ส่งรหัสผ่านใหม่ให้ User <br>5. สร้าง `AdminLog` บันทึก action |
| **Main Flow (Reject)** | 1. Admin คลิก Reject <br>2. ระบบอัปเดต status = Rejected <br>3. สร้าง `Notification` แจ้ง User |
| **Postcondition** | `PasswordResetRequest.status` อัปเดต + `Notification` สร้าง |

---

### UC-A07 — Mark Alert อ่านแล้ว

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `POST /admin-dashboard/alerts/<alert_id>/mark-read/` |
| **View** | `mark_alert_read` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. Admin คลิก mark อ่าน <br>2. ระบบตั้ง `Alert.is_read = True` |
| **Postcondition** | Alert ถูก mark อ่านแล้ว |

---

### UC-A08 — Refresh Association Rules Cache

| Field | Detail |
|---|---|
| **Actor** | Admin |
| **Route** | `POST /api/admin/refresh-rules/` |
| **View** | `api_refresh_association_rules` |
| **Precondition** | Login เป็น Admin |
| **Main Flow** | 1. Admin POST ขอ refresh <br>2. ระบบรัน Apriori algorithm ใหม่จาก ProPlayer + Gear ใน DB <br>3. เขียนผลลัพธ์ลง Django Cache (TTL 24h ใหม่) |
| **Alternative Flow** | 2a. ข้อมูลไม่เพียงพอ (Pro Player < threshold) → return 400 |
| **Postcondition** | Cache อัปเดต, Association Rules ใหม่พร้อมใช้งาน |

---

## สรุปจำนวน Use Cases

| กลุ่ม | จำนวน |
|---|---|
| Guest (UC-G) | 14 |
| Member (UC-M) | 18 |
| Admin (UC-A) | 8 |
| **รวม** | **40** |
