# Gaming Gear Matcher — Developer Guide

> **Status:** Draft (skeleton)
> **Last updated:** 2026-02-23
> **Stack:** Django 5.1 · PostgreSQL 15 · Docker · mlxtend

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Prerequisites](#3-prerequisites)
4. [Getting Started](#4-getting-started)
   - 4.1 [Clone & Environment Setup](#41-clone--environment-setup)
   - 4.2 [Running with Docker (Recommended)](#42-running-with-docker-recommended)
   - 4.3 [Running Locally (Without Docker)](#43-running-locally-without-docker)
5. [Project Structure](#5-project-structure)
6. [Environment Variables](#6-environment-variables)
7. [Database](#7-database)
   - 7.1 [Data Models & Relationships](#71-data-models--relationships)
   - 7.2 [Migrations](#72-migrations)
   - 7.3 [Seeding / Importing Data](#73-seeding--importing-data)
8. [Authentication & Roles](#8-authentication--roles)
   - 8.1 [Role System](#81-role-system)
   - 8.2 [Allauth Integration](#82-allauth-integration)
   - 8.3 [Banned User Flow](#83-banned-user-flow)
9. [URL Routes & Access Control](#9-url-routes--access-control)
   - 9.1 [Public Routes](#91-public-routes)
   - 9.2 [Member Routes](#92-member-routes)
   - 9.3 [Admin Routes](#93-admin-routes)
   - 9.4 [API Endpoints](#94-api-endpoints)
10. [Recommender Engine](#10-recommender-engine)
    - 10.1 [Hybrid Recommender](#101-hybrid-recommender)
    - 10.2 [Association Rule Mining (Apriori)](#102-association-rule-mining-apriori)
    - 10.3 [Caching Strategy](#103-caching-strategy)
11. [Wizard / Matching Flow](#11-wizard--matching-flow)
12. [Admin Panel (Custom)](#12-admin-panel-custom)
13. [Media & Static Files](#13-media--static-files)
14. [Management Commands](#14-management-commands)
15. [API Reference](#15-api-reference)
16. [Testing](#16-testing)
17. [Code Conventions](#17-code-conventions)
18. [Deployment](#18-deployment)
    - 18.1 [Docker Production](#181-docker-production)
    - 18.2 [Environment Checklist](#182-environment-checklist)
19. [Troubleshooting](#19-troubleshooting)
20. [Contributing](#20-contributing)

---

## 1. Project Overview

**Gaming Gear Matcher** คือเว็บแอปพลิเคชันที่ช่วยให้นักเล่นเกมค้นหาและจับคู่อุปกรณ์เกมมิ่ง (Gaming Gear) ที่เหมาะสมกับตัวเองมากที่สุด โดยอ้างอิงข้อมูลจากนักกีฬา Esports มืออาชีพ (Pro Players) และวิเคราะห์จาก Playstyle ส่วนตัวของผู้ใช้

### ปัญหาที่แก้

นักเล่นเกมส่วนใหญ่ไม่รู้ว่าควรเลือก Mouse, Keyboard, Headset, Monitor หรือเก้าอี้รุ่นไหน เพราะตัวเลือกมีมากและสเปคมีความซับซ้อน ระบบนี้จึงทำหน้าที่เป็น "ที่ปรึกษา" ที่แนะนำอุปกรณ์แบบ personalized

### ผู้ใช้งานหลัก

| Actor | คำอธิบาย |
|---|---|
| **Guest** | เข้าดูข้อมูล Gear, Pro Player และทำ Wizard จับคู่ Gear ได้โดยไม่ต้อง Login |
| **Member** | บันทึก Preset, ให้คะแนน, แชร์ชุดอุปกรณ์ และรับ Notification |
| **Admin** | จัดการข้อมูล Gear, Pro Player, Member รวมถึงดู Dashboard ภาพรวม |

### คุณสมบัติหลัก

**Wizard & Gear Matching**
- ผู้ใช้ตอบแบบสอบถาม Playstyle 3 ข้อ: ประเภทเกม (genre), ขนาดมือ (hand_size), วิธีจับเมาส์ (grip)
- ระบบประมวลผลด้วย `HybridRecommender` และแสดงผล 3 Variant: **Performance**, **Balanced**, **Pro Choice**

**Recommender Engine — HybridRecommender**

ใช้ Rule-based Scoring แยกตามประเภทอุปกรณ์:

| อุปกรณ์ | ปัจจัยหลักในการให้คะแนน |
|---|---|
| Mouse | ขนาดมือ → ความยาว Mouse, Grip Style → Shape, Genre → น้ำหนัก, Sentiment Score |
| Keyboard | Genre → Form Factor (60%/TKL/Full Size), Sentiment Score |
| Headset | Sentiment Score (เสียงเป็นเรื่อง Subjective) |
| Monitor | Genre → Refresh Rate (FPS ต้องการ 240Hz+), Resolution (RPG ต้องการ 1440p+), Panel Tech |
| Chair | ขนาดมือเป็น proxy ของขนาดตัว, Material, Lumbar Support, Sentiment Score |

**Recommender Engine — Association Rules (Apriori)**
- วิเคราะห์ pattern จาก Preset ของ User ทั้งหมดด้วย Market Basket Analysis
- ค้นหาว่า "คนที่เลือก Gear A มักเลือก Gear B ด้วย" เพื่อแนะนำ Gear เพิ่มเติม
- ใช้ library `mlxtend` กับ parameter: `min_support=0.05`, `min_confidence=0.3`, `min_lift=1.0`
- Cache ผลไว้ 24 ชั่วโมง

**Preset Management**
- Member บันทึกชุดอุปกรณ์เป็น Preset, แชร์ผ่าน UUID link, ให้คะแนน 1–5 ดาว และสลับ Gear แต่ละชิ้นได้

**Pro Player Database**
- เก็บข้อมูล Pro Player พร้อม settings, eDPI, sensitivity และ Gear ที่ใช้จริง
- ผู้ใช้ดึง Gear ทั้งหมดของ Pro Player มาสร้าง Preset ของตัวเองได้ทันที

**Admin Panel (Custom)**
- Dashboard แสดงสถิติ, จัดการ Gear/Pro Player/Member, ระบบ Ban User, รับคำขอ Reset Password และบันทึก Audit Log ทุก action

### Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Django 5.1 |
| Database | PostgreSQL 15 (GIN Index บน JSONField specs) |
| Authentication | django-allauth (Username/Email + Google OAuth) |
| Recommender | Custom Rule-based + mlxtend (Apriori) |
| Static Files | WhiteNoise |
| Containerization | Docker + Docker Compose |
| Runtime | Python 3.11, Gunicorn (production) |

## 2. Architecture Overview

ดู diagram แบบเต็มได้ที่ [arch.puml](arch.puml) และ flowchart ของ Recommender ที่ [recommender_flow.puml](recommender_flow.puml)

### 2.1 ภาพรวมระบบ

```
Browser (Guest / Member / Admin)
        │  HTTP
        ▼
┌─────────────────────────────────┐   Docker: gaming_gear_network
│  Web Container: gaming_gear_web │
│  ┌───────────────────────────┐  │
│  │      Django Application   │  │
│  │  urls.py → views.py       │  │
│  │  api_views.py (REST)      │  │
│  │  HybridRecommender        │  │
│  │  AssociationRuleMiner     │  │
│  └───────────────────────────┘  │
│  port 8000                      │
└────────────────┬────────────────┘
                 │ psycopg2 / port 5432
                 ▼
┌─────────────────────────────────┐
│  DB Container: gaming_gear_db   │
│  PostgreSQL 15                  │
│  volume: postgres_data          │
└─────────────────────────────────┘
```

### 2.2 Docker Services

| Service | Container | Image | Port |
|---|---|---|---|
| `web` | `gaming_gear_web` | Python 3.11-slim (multi-stage build) | 8000 |
| `db` | `gaming_gear_db` | postgres:15-alpine | 5432 |

- `web` ขึ้นได้ก็ต่อเมื่อ `db` ผ่าน healthcheck (`pg_isready`) แล้วเท่านั้น (`depends_on: condition: service_healthy`)
- `postgres_data` เป็น named volume ทำให้ข้อมูลไม่หายเมื่อ restart container
- Code mount แบบ volume (`.:/app`) ในโหมด dev ทำให้แก้ไขไฟล์แล้วเห็นผลทันทีโดยไม่ต้อง rebuild

### 2.3 Request Lifecycle

```
1. Browser → HTTP Request (port 8000)
2. Django Middleware Stack (ตามลำดับ):
     SecurityMiddleware
     WhiteNoiseMiddleware       ← serve static files
     SessionMiddleware
     CommonMiddleware
     CsrfViewMiddleware
     AuthenticationMiddleware
     BannedUserMiddleware       ← kick ถ้า is_active=False
     AccountMiddleware (allauth)
     MessageMiddleware
     XFrameOptionsMiddleware
3. URL Router (GamingGearMatcher/urls.py)
     ├── /admin/          → Django Admin
     ├── /accounts/       → allauth (Google OAuth, password reset)
     └── /               → APP01/urls.py
           ├── HTML routes → views.py
           └── /api/*     → api_views.py
4. View → ORM → PostgreSQL
5. View → Template → HTTP Response
```

### 2.4 โครงสร้าง Layer

| Layer | ไฟล์หลัก | หน้าที่ |
|---|---|---|
| **Routing** | [GamingGearMatcher/urls.py](GamingGearMatcher/urls.py), [APP01/urls.py](APP01/urls.py) | แมป URL → View |
| **Views (HTML)** | [APP01/views.py](APP01/views.py) | รับ request, เรียก logic, render template |
| **Views (API)** | [APP01/api_views.py](APP01/api_views.py) | REST endpoint ส่ง JSON |
| **Business Logic** | [APP01/recommender_hybrid.py](APP01/recommender_hybrid.py), [APP01/association_rules.py](APP01/association_rules.py) | Recommender Engine |
| **Data Models** | [APP01/models.py](APP01/models.py) | ORM กับ PostgreSQL |
| **Forms** | [APP01/forms.py](APP01/forms.py) | Validation input จาก user |
| **Middleware** | [APP01/middleware.py](APP01/middleware.py) | Ban check ทุก request |
| **Auth Adapter** | [APP01/adapter.py](APP01/adapter.py) | ปรับ allauth ให้ใช้ Custom User |
| **Templates** | [APP01/templates/APP01/](APP01/templates/APP01/) | HTML (Django template engine) |
| **Static** | WhiteNoise | serve CSS/JS ใน production |
| **Media** | `media/` volume | ไฟล์ที่ user upload (รูปภาพ) |

### 2.5 Recommender Architecture

ระบบมี Recommender Engine สองตัวที่ทำงานแยกกัน:

```
Wizard Quiz (genre, hand_size, grip)
        │
        ▼
┌─────────────────────────┐
│   HybridRecommender     │  ← Rule-based scoring
│   recommend_variant_    │     ต่อ category ต่อ user
│   setups(user_prefs)    │
└──────────┬──────────────┘
           │ Top 5 candidates/category
           ▼
  Performance │ Balanced │ Pro Choice
  (index 0)   │(index 1) │(most used by pros)
        │
        ▼
   Session Storage → matching_result.html


Preset ของ Users ทุกคน
        │
        ▼
┌─────────────────────────┐
│  AssociationRuleMiner   │  ← Apriori algorithm
│  (mlxtend)              │     Market Basket Analysis
│  Cache 24h              │
└──────────┬──────────────┘
           │ Association Rules
           ▼
  POST /api/recommendations/
  (แนะนำ Gear เพิ่มเติมจาก Gear ที่เลือกไปแล้ว)
```

### 2.6 Database Schema (ภาพรวม)

```
Role ──< User >──────────── Notification
              │
              ├──< Preset >──── PresetGear >── GamingGear
              │        │                            │
              │   PresetRating             ProPlayerGear
              │                                     │
              └── AdminLog           ProPlayer >────┘
                                          │
              PasswordResetRequest      Game
              Alert
```

ความสัมพันธ์สำคัญ:

| Relation | ประเภท | หมายเหตุ |
|---|---|---|
| `User` → `Role` | FK | กำหนดสิทธิ์ Admin / Member |
| `Preset` → `User` | FK | Preset เป็นของ User คนเดียว |
| `PresetGear` | Junction (M2M) | Preset ↔ GamingGear มีฟิลด์ `order` |
| `ProPlayerGear` | Junction (M2M) | ProPlayer ↔ GamingGear |
| `GamingGear.specs` | JSONField | สเปคทุกอย่าง มี GIN Index |
| `Preset.share_link` | UUID | สร้างอัตโนมัติเมื่อ save |

## 3. Prerequisites

<!--
TODO: ระบุ version ที่ต้องการ
-->

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Docker & Docker Compose | 24+ |
| PostgreSQL (local) | 15+ |

## 4. Getting Started

### 4.1 Clone & Environment Setup

```bash
# TODO: เพิ่ม repo URL
git clone <repo-url>
cd Gaming-Gear-Matcher-Project

cp .env.example .env  # TODO: สร้าง .env.example
# แก้ไข .env ตามที่ต้องการ (ดู Section 6)
```

### 4.2 Running with Docker (Recommended)

```bash
# Build และเริ่ม services ทั้งหมด
docker compose up --build

# รัน migrations ครั้งแรก
docker compose exec web python manage.py migrate

# สร้าง superuser
docker compose exec web python manage.py createsuperuser

# Import ข้อมูลตัวอย่าง
docker compose exec web python manage.py import_real_data
```

เปิดที่ http://localhost:8000

### 4.3 Running Locally (Without Docker)

```bash
# สร้าง virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# ติดตั้ง dependencies
pip install -r requirements.txt

# ตั้งค่า DB ใน .env ให้ชี้ไปที่ PostgreSQL local
# หรือปล่อยให้ fallback เป็น SQLite (ดู settings.py)

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 5. Project Structure

### 5.1 โครงสร้างไดเรกทอรี

```
Gaming-Gear-Matcher-Project/
├── GamingGearMatcher/          # Django project config (settings, root URLs, WSGI/ASGI)
│   ├── settings.py             # ← ตั้งค่าทั้งหมด: DB, Auth, Cache, Middleware
│   ├── urls.py                 # ← Root URL: /admin/, /accounts/, / (APP01)
│   ├── wsgi.py                 # Gunicorn entry point (production)
│   └── asgi.py                 # ASGI entry point (async, ไม่ได้ใช้จริงในปัจจุบัน)
│
├── APP01/                      # Django application หลัก
│   ├── models.py               # 13 ORM Models (User, GamingGear, Preset, ฯลฯ)
│   ├── views.py                # HTML views ทุก route (login, wizard, preset CRUD, admin)
│   ├── api_views.py            # REST JSON endpoints (/api/recommendations/, /api/admin/refresh-rules/)
│   ├── urls.py                 # URL routing ของ APP01 (40 patterns)
│   ├── forms.py                # Django Forms (Login, Register, ProPlayer, GamingGear, Preset, UserEdit)
│   ├── recommender_hybrid.py   # HybridRecommender — Rule-based scoring engine
│   ├── association_rules.py    # AssociationRuleMiner — Apriori / Market Basket Analysis
│   ├── middleware.py           # BannedUserMiddleware — kick ผู้ใช้ที่ถูก ban
│   ├── adapter.py              # Allauth adapters (Account + Social)
│   ├── admin.py                # ลงทะเบียน models กับ Django Admin
│   ├── apps.py                 # AppConfig
│   ├── migrations/             # Database migration files (auto-generated)
│   ├── templates/APP01/        # HTML templates (Django template engine)
│   ├── templatetags/           # Custom template filters
│   │   └── custom_filters.py   # get_item, get_spec, split
│   ├── static/                 # Static assets ของ app (CSS, JS, images)
│   └── management/
│       └── commands/
│           └── import_real_data.py  # Management command: นำเข้าข้อมูล Gear + ProPlayer จาก JSON
│
├── data/                       # ไฟล์ข้อมูล JSON (offline, ไม่ใช่ runtime)
│   ├── gaming_gear.json        # ข้อมูล GamingGear สำหรับ import
│   └── pro_players.json        # ข้อมูล ProPlayer สำหรับ import
│
├── media/                      # ไฟล์ที่ user upload (รูปภาพ Gear, ProPlayer)
│                               # → mounted เป็น Docker volume (./media:/app/media)
│
├── staticfiles/                # Static files รวมหลัง `collectstatic`
│                               # → served โดย WhiteNoise ใน production
│
├── docker-compose.yml          # กำหนด services: web (port 8000), db (port 5432)
├── Dockerfile                  # Multi-stage build: deps → production image
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (ห้าม commit ลง git)
└── arch.puml                   # System architecture diagram (PlantUML)
```

---

### 5.2 GamingGearMatcher/ — Project Config

#### `settings.py`

ตั้งค่าหลักของโปรเจกต์:

| หมวด | การตั้งค่าที่สำคัญ |
|---|---|
| **Auth** | `AUTH_USER_MODEL = 'APP01.User'` — ใช้ Custom User แทน Django default |
| **Apps** | รวม `allauth`, `allauth.socialaccount`, `allauth.socialaccount.providers.google` |
| **Middleware** | 10 middleware ในลำดับที่กำหนด (ดู Section 2.3) |
| **Database** | PostgreSQL ผ่าน `dj-database-url` / fallback SQLite ถ้าไม่มี `POSTGRES_PASSWORD` |
| **Cache** | `DatabaseCache` (table `django_cache`) ใน production, `LocMemCache` ใน dev |
| **Static** | `STATICFILES_STORAGE = WhiteNoiseStorage` |
| **Auth Adapters** | `ACCOUNT_ADAPTER = 'APP01.adapter.MyAccountAdapter'` |
| **Time zone** | `TIME_ZONE = 'Asia/Bangkok'` |
| **Login/Logout** | `LOGIN_URL = '/login/'`, `LOGIN_REDIRECT_URL = '/'` |

#### `urls.py`

Root URL configuration มี 3 กลุ่ม:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    # Override accounts/inactive/ ก่อน allauth (custom ban page)
    path('accounts/inactive/', app01_views.custom_account_inactive, name='account_inactive'),
    path('accounts/', include('allauth.urls')),   # Google OAuth, password reset
    path('', include('APP01.urls')),              # ทุก route อื่น ๆ
]
```

---

### 5.3 APP01/ — Main Application

#### `models.py` — 13 Data Models

| Model | หน้าที่ | Fields ที่น่าสนใจ |
|---|---|---|
| `Role` | บทบาท Admin / Member | `role_name` |
| `User` | Custom user (AbstractBaseUser) | `username`, `email`, `role` (FK), `is_active` (ban flag) |
| `Game` | ชื่อเกม + โลโก้ | `game_name`, `logo` |
| `ProPlayer` | นักกีฬา Esports | `game` (FK), `mouse_sensitivity`, `dpi`, `edpi` |
| `GamingGear` | อุปกรณ์ทุกประเภท | `type` (Mouse/Keyboard/…), `specs` (JSONField + GIN Index) |
| `ProPlayerGear` | Junction: ProPlayer ↔ GamingGear | `player`, `gear` |
| `Preset` | ชุดอุปกรณ์ของ User | `user` (FK), `share_link` (UUID, auto-generated) |
| `PresetGear` | Junction: Preset ↔ GamingGear | `preset`, `gear`, `order` |
| `PresetRating` | คะแนน 1–5 ดาว | `user`, `preset`, `rating` |
| `Alert` | การแจ้งเตือนระดับระบบ (Admin เห็น) | `message`, `alert_type`, `is_read` |
| `AdminLog` | Log การกระทำของ Admin | `admin`, `action`, `target_user`, `created_at` |
| `Notification` | ข้อความแจ้งเตือนถึง User | `user`, `message`, `is_read` |
| `PasswordResetRequest` | คำขอรีเซ็ตรหัสผ่าน | `status` (Pending/Approved/Rejected) |

**จุดสำคัญ:**
- `User` ใช้ `CustomUserManager` ที่ auto-assign Role "Member" เมื่อ `create_user()`
- `GamingGear.specs` เป็น JSONField มี `GinIndex` เพื่อ query ใน JSON ได้เร็ว
- `Preset.save()` override เพื่อสร้าง `share_link` (UUID) อัตโนมัติถ้ายังไม่มี

---

#### `views.py` — HTML Views

แบ่งตามกลุ่มฟังก์ชัน:

| กลุ่ม | Views | หน้าที่ |
|---|---|---|
| **Auth** | `login_view`, `register_view`, `logout_view`, `custom_account_inactive` | Login/Register/Logout/Ban page |
| **Wizard** | `start_matching`, `wizard_quiz`, `process_quiz`, `matching_result` | ขั้นตอนแนะนำอุปกรณ์ (quiz → result) |
| **Preset** | `save_preset`, `preset_detail`, `preset_list`, `edit_preset`, `delete_preset`, `share_preset`, `rate_preset`, `use_all_gears` | CRUD + Share + Rating |
| **Catalog** | `gear_list`, `gear_detail`, `proplayer_list`, `proplayer_detail`, `search_results` | ดูอุปกรณ์ / นักกีฬา |
| **Profile** | `profile_view`, `edit_profile`, `change_password` | จัดการโปรไฟล์ user |
| **Admin** | `admin_dashboard`, `admin_users`, `admin_gear`, `admin_proplayer`, `admin_alerts`, `admin_password_requests` | หน้าจัดการ Admin |
| **Helper** | `is_admin()`, `is_member()` | ตรวจสอบ role สำหรับ decorator |

**Wizard Flow (สำคัญ):**

```
start_matching → wizard_quiz (GET: แสดง quiz)
                           ↓ (POST: submit genre, hand_size, grip)
              process_quiz → HybridRecommender.recommend_variant_setups()
                           → เก็บใน session["wizard_preset"] + session["variants_data"]
                           → redirect matching_result
              matching_result → แสดง 3 variants: Performance / Balanced / Pro Choice
```

---

#### `api_views.py` — REST API Endpoints

มี 2 endpoints:

| Endpoint | Method | Auth | หน้าที่ |
|---|---|---|---|
| `/api/recommendations/` | POST | `@login_required` | รับ `gear_ids`, `top_n`, `exclude_types` → ส่งคืน Gear ที่แนะนำจาก Association Rules |
| `/api/admin/refresh-rules/` | POST | `@login_required` + is_admin check | สั่ง re-mine Apriori rules และ refresh Django Cache |

เรียกใช้จาก JS `fetch()` ใน Wizard หน้า `wizard_quiz.html` ทุกครั้งที่ user เลือก Gear

---

#### `forms.py` — Django Forms

| Form | ใช้ที่ | หน้าที่สำคัญ |
|---|---|---|
| `LoginForm` | `login_view` | Username + Password |
| `RegisterForm` | `register_view` | ตรวจสอบ email ซ้ำ, auto-assign Role "Member" |
| `ProPlayerForm` | `admin_proplayer` | `gears_text` (ชื่อ Gear คั่น comma → parse → link กับ GamingGear) |
| `GamingGearForm` | `admin_gear` | ฟอร์ม CRUD Gear (มี specs JSONField) |
| `PresetForm` | `save_preset`, `edit_preset` | ชื่อ + คำอธิบาย Preset |
| `UserEditForm` | `edit_profile` (admin) | แก้ไขข้อมูล user |

---

#### `recommender_hybrid.py` — HybridRecommender

Rule-based scoring engine (ไม่ใช่ ML จริง):

```
recommend_variant_setups(user_prefs)
  ├── recommend_mouse()     → score: HandSize(+30) + Grip(+30) + Genre(+35) + Sentiment(+15) = max 110
  ├── recommend_keyboard()  → score: Genre×FormFactor(+35) + Sentiment(+20) = max 55
  ├── recommend_headset()   → score: Sentiment×4 = max 60
  ├── recommend_monitor()   → score: Genre→Hz/Resolution(+40) + Sentiment(+20) = max 60
  └── recommend_chair()     → score: HandSize proxy(+20) + Material(+15) + Lumbar(+10) + Sentiment(+30) = max 75

Build Variants:
  Performance → index[0] ของทุก category, score normalize /305×100
  Balanced    → index[1] ของทุก category (fallback index[0])
  Pro Choice  → gear ที่มีจำนวน ProPlayer ใช้มากที่สุด (COUNT annotate), score fixed=95
```

---

#### `association_rules.py` — AssociationRuleMiner

Apriori algorithm สำหรับ Gear recommendation:

```
Singleton: get_miner() → AssociationRuleMiner instance

build_transaction_data()
  → ProPlayer.objects.prefetch_related('proplayergear_set__gear')
  → Transaction = ProPlayer, Item = gear_id
  → กรองเฉพาะ player ที่มี >= 2 gears
  → TransactionEncoder → one-hot DataFrame

mine_association_rules()
  → apriori(min_support=0.05) → frequent_itemsets
  → association_rules(min_confidence=0.3) → rules
  → filter: lift >= 1.0
  → sort by: confidence × lift (score)

get_recommendations(gear_ids, top_n, exclude_types)
  → ดึง rules จาก Cache (key: "association_rules_rules", TTL=24h)
  → หา rules ที่ antecedents ⊆ gear_ids ที่เลือก
  → realistic_confidence = 0.70 + (confidence × 0.25)
  → Fallback: popular gears จาก COUNT('proplayergear') ถ้าผลน้อยกว่า top_n
```

---

#### `middleware.py` — BannedUserMiddleware

```python
# ทำงานทุก request หลัง AuthenticationMiddleware
if request.user.is_authenticated and not request.user.is_active:
    auth.logout(request)
    redirect('/login/')  # พร้อม flash message "บัญชีถูกระงับ พร้อม ban date"
```

อ่าน `ban_date` จาก `AdminLog` (action="ban") ของ user นั้น

---

#### `adapter.py` — Allauth Adapters

| Class | หน้าที่ |
|---|---|
| `MyAccountAdapter` | Override `respond_user_inactive()` → ดึง `ban_date` จาก AdminLog แสดงใน redirect |
| `MySocialAccountAdapter` | จัดการ error เมื่อ Google OAuth ล้มเหลว (email ซ้ำ, account ถูก ban) |

---

#### `templatetags/custom_filters.py` — Template Filters

| Filter | Signature | หน้าที่ |
|---|---|---|
| `get_item` | `dict\|get_item:key` | อ่านค่าจาก dict ใน template อย่างปลอดภัย |
| `get_spec` | `gear\|get_spec:key` | อ่านสเปคจาก `GamingGear.specs` (JSONField หรือ string) |
| `split` | `string\|split:delimiter` | แบ่ง string ด้วย delimiter ใน template |

ใช้ใน templates ที่ต้องแสดง specs ที่เก็บใน JSONField เช่น `{{ gear|get_spec:"Weight" }}`

---

#### `management/commands/import_real_data.py`

Management command สำหรับ load ข้อมูลตัวอย่าง:

```bash
python manage.py import_real_data
```

- อ่านจาก `data/gaming_gear.json` → สร้าง `GamingGear` objects
- อ่านจาก `data/pro_players.json` → สร้าง `ProPlayer` + link `ProPlayerGear`
- มี `generate_description()` ที่สร้างคำอธิบาย Gear จาก specs อัตโนมัติ
- ใช้ `update_or_create()` ทำให้รัน idempotent (ปลอดภัย รันซ้ำได้)

---

### 5.4 Templates

Templates อยู่ที่ [APP01/templates/APP01/](APP01/templates/APP01/) แบ่งตามหน้า:

| Template | Route | หน้าที่ |
|---|---|---|
| `base.html` | - | Base template ที่ทุกหน้า extend |
| `login.html` / `register.html` | `/login/` `/register/` | Auth pages |
| `wizard_quiz.html` | `/wizard/quiz/` | Wizard + JS fetch สำหรับ `/api/recommendations/` |
| `matching_result.html` | `/matching-result/` | แสดง 3 Variant tabs |
| `preset_list.html` / `preset_detail.html` | `/presets/` | Preset management |
| `gear_list.html` / `gear_detail.html` | `/gears/` | Gear catalog |
| `proplayer_list.html` / `proplayer_detail.html` | `/proplayers/` | Pro Player catalog |
| `admin_*.html` | `/admin-panel/` | Admin management pages |
| `profile.html` / `edit_profile.html` | `/profile/` | User profile |

---

### 5.5 data/ — Import Data (Offline)

ไดเรกทอรีนี้ **ไม่ได้ใช้ใน runtime** — เป็นแค่ข้อมูล JSON สำหรับ import ครั้งเดียว:

```
data/
├── gaming_gear.json     # รายการ Gear พร้อม specs
└── pro_players.json     # รายการ ProPlayer พร้อม gear ที่ใช้
```

ใช้ร่วมกับ `python manage.py import_real_data`

## 6. Environment Variables

| Variable | Default | คำอธิบาย |
|---|---|---|
| `DEBUG` | `True` | เปิด/ปิด debug mode |
| `SECRET_KEY` | (insecure default) | Django secret key — **ต้องเปลี่ยนใน production** |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts ที่อนุญาต |
| `POSTGRES_DB` | `gaming_gear_matcher` | ชื่อ database |
| `POSTGRES_USER` | `postgres` | DB user |
| `POSTGRES_PASSWORD` | - | DB password (ถ้าว่าง จะ fallback เป็น SQLite) |
| `POSTGRES_HOST` | `localhost` | DB host (`db` ใน Docker) |
| `POSTGRES_PORT` | `5432` | DB port |
| `SECURE_SSL_REDIRECT` | `False` | บังคับ HTTPS (production) |

## 7. Database

### 7.1 Data Models & Relationships

<!--
TODO: อธิบาย ERD / ความสัมพันธ์ระหว่าง Model
-->

| Model | คำอธิบาย |
|---|---|
| `Role` | บทบาท: Admin / Member |
| `User` | Custom user model (AbstractBaseUser) |
| `Game` | ชื่อเกม + โลโก้ |
| `ProPlayer` | นักกีฬา Esports + settings, eDPI |
| `GamingGear` | อุปกรณ์ (Mouse/Keyboard/Headset/Monitor/Chair) + specs (JSONField) |
| `ProPlayerGear` | Many-to-Many: ProPlayer ↔ GamingGear |
| `Preset` | ชุดอุปกรณ์ของ User (มี share_link) |
| `PresetGear` | Many-to-Many: Preset ↔ GamingGear (มี order) |
| `PresetRating` | คะแนน 1–5 ดาวที่ User ให้ Preset |
| `Alert` | การแจ้งเตือนระดับระบบสำหรับ Admin |
| `AdminLog` | Log การกระทำของ Admin |
| `Notification` | ข้อความแจ้งเตือนถึง User |
| `PasswordResetRequest` | คำขอรีเซ็ตรหัสผ่าน (Pending/Approved/Rejected) |

### 7.2 Migrations

```bash
# สร้าง migration ใหม่หลังแก้ models.py
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# ดู migration history
python manage.py showmigrations
```

### 7.3 Seeding / Importing Data

```bash
# Import Pro Player + Gear จากข้อมูลจริง
python manage.py import_real_data

# อัปเดตราคา Gear
python manage.py update_gear_prices
```

## 8. Authentication & Roles

### 8.1 Role System

<!--
TODO: อธิบาย is_admin() / is_member() helper functions
-->

- **Admin** — `is_superuser=True` หรือ `role.role_name='Admin'`
- **Member** — `role.role_name='Member'` (กำหนดอัตโนมัติตอน register)

### 8.2 Allauth Integration

- ใช้ `django-allauth` สำหรับ authentication flow
- Custom adapter: `APP01.adapter.MyAccountAdapter` / `MySocialAccountAdapter`
- รองรับ Google OAuth (`allauth.socialaccount.providers.google`)

### 8.3 Banned User Flow

- Middleware: `APP01.middleware.BannedUserMiddleware`
- ตรวจสอบ `user.is_active` ทุก request
- Admin toggle ban ผ่าน `/admin-dashboard/members/<id>/toggle-status/`

## 9. URL Routes & Access Control

### 9.1 Public Routes

<!--  TODO: ดูตาราง route ที่สรุปไว้ใน arch.puml / README -->

### 9.2 Member Routes

<!-- TODO -->

### 9.3 Admin Routes

<!-- TODO -->

### 9.4 API Endpoints

| Method | Endpoint | Auth | คำอธิบาย |
|---|---|---|---|
| POST | `/api/recommendations/` | Login required | แนะนำ Gear ด้วย Association Rules |
| POST | `/api/admin/refresh-rules/` | Admin only | Refresh cache |

## 10. Recommender Engine

### 10.1 Hybrid Recommender

<!--
TODO: อธิบาย HybridRecommender class ใน recommender_hybrid.py
- Input: user_prefs (genre, hand_size, grip)
- Output: variant setups (Performance / Budget / ProStyle)
- Logic: Rule-based spec matching per gear category
-->

### 10.2 Association Rule Mining (Apriori)

<!--
TODO: อธิบาย AssociationRuleMiner ใน association_rules.py
- ใช้ mlxtend.frequent_patterns.apriori
- ข้อมูล: transaction = Preset ↔ GamingGear
- Parameters: min_support=0.05, min_confidence=0.3, min_lift=1.0
-->

### 10.3 Caching Strategy

- Association rules ถูก cache ไว้ที่ Django cache (key: `association_rules_*`)
- TTL: **24 ชั่วโมง**
- Dev: in-memory cache | Production: DatabaseCache (`cache_table`)
- Refresh ด้วย: `POST /api/admin/refresh-rules/`

## 11. Wizard / Matching Flow

<!--
TODO: อธิบาย step-by-step ของ Wizard
1. GET  /start-matching/         → wizard_start.html
2. GET  /wizard/quiz/            → quiz.html (genre, hand_size, grip)
3. POST /wizard/process-quiz/    → run HybridRecommender → เก็บใน session
4. GET  /wizard/select/<cat>/    → เลือก Gear ทีละ category
5. GET  /matching-result/        → แสดงผล + Variant tabs
6. POST /preset/save/            → บันทึกเป็น Preset (Member เท่านั้น)
-->

## 12. Admin Panel (Custom)

<!--
TODO: อธิบาย custom admin (ไม่ใช่ Django admin แต่เป็น /admin-dashboard/)
- Dashboard: สถิติ User, Gear, ProPlayer
- จัดการ Gear, Pro Player, Members (ban/unban)
- Password Reset Requests
- AdminLog (audit trail)
-->

## 13. Media & Static Files

```
media/
├── user_profiles/    # รูปโปรไฟล์ User
├── gaming_gears/     # รูป Gaming Gear
├── pro_players/      # รูป Pro Player
└── game_logos/       # โลโก้ Game
```

- Dev: serve โดย Django (`MEDIA_URL=/media/`)
- Production: ควรใช้ CDN หรือ object storage (S3)
- Static: จัดการโดย WhiteNoise (`whitenoise.storage.CompressedManifestStaticFilesStorage`)

## 14. Management Commands

| Command | คำอธิบาย |
|---|---|
| `import_real_data` | Import Pro Player + Gear จาก fixtures |
| `update_gear_prices` | อัปเดตราคา Gear จาก `gear_prices_data.py` |

```bash
python manage.py <command> [options]
```

## 15. API Reference

<!--
TODO: เพิ่ม request/response schema สำหรับแต่ละ endpoint
-->

### POST `/api/recommendations/`

**Request:**
```json
{
  "gear_ids": [1, 3, 7],
  "top_n": 5,
  "exclude_types": ["Chair"]
}
```

**Response:**
```json
{
  "success": true,
  "recommendations": [
    {
      "gear_id": 12,
      "name": "...",
      "type": "Keyboard",
      "confidence": 75.0,
      "lift": 2.3,
      "score": 1.73
    }
  ],
  "count": 1
}
```

## 16. Testing

```bash
# รัน test ทั้งหมด
python manage.py test APP01

# TODO: เพิ่ม test cases ใน APP01/tests.py
```

<!--
TODO: อธิบาย test strategy
- Unit test: Models, Recommender logic
- Integration test: Views, API endpoints
-->

## 17. Code Conventions

<!--
TODO: กำหนด coding style
-->

- **Python:** PEP 8, ใช้ `djlint` สำหรับ template linting
- **Views:** แยก HTML views (`views.py`) กับ API views (`api_views.py`)
- **Models:** ใช้ `AutoField` primary key, ระบุ `related_name` ทุกครั้งที่มี FK ซ้ำ
- **Templates:** อยู่ใน `APP01/templates/APP01/`
- **Secrets:** ห้าม commit `.env` — ใช้ `.env.example` แทน

## 18. Deployment

### 18.1 Docker Production

```bash
# TODO: เพิ่ม docker-compose.prod.yml แยกต่างหาก
docker compose -f docker-compose.prod.yml up -d

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createcachetable  # สำหรับ DatabaseCache
```

### 18.2 Environment Checklist

- [ ] เปลี่ยน `SECRET_KEY` เป็น random string ที่ปลอดภัย
- [ ] ตั้ง `DEBUG=False`
- [ ] กำหนด `ALLOWED_HOSTS` ให้ถูกต้อง
- [ ] ตั้งค่า Email SMTP (แทน console backend)
- [ ] เปิด `SECURE_SSL_REDIRECT=True`
- [ ] รัน `python manage.py createcachetable`
- [ ] ตั้งค่า Media storage (S3 หรือ volume ถาวร)
- [ ] Backup strategy สำหรับ `postgres_data` volume

## 19. Troubleshooting

<!--
TODO: รวบรวมปัญหาที่พบบ่อย
-->

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| `FATAL: role "postgres" does not exist` | DB ยังไม่พร้อม | รอ healthcheck ผ่านก่อน (`depends_on: condition: service_healthy`) |
| Static files ไม่แสดง | ยังไม่ได้ run `collectstatic` | `python manage.py collectstatic` |
| Association rules ว่างเปล่า | ข้อมูล Preset น้อยเกินไป | เพิ่ม Preset หรือลด `min_support` |
| `OperationalError` บน Notification | Migration ยังไม่ครบ | `python manage.py migrate` |

## 20. Contributing

<!--
TODO: กำหนด branching strategy, PR process, review checklist
-->

1. ตัด branch จาก `main`: `git checkout -b feature/<ชื่อ-feature>`
2. เขียน code + test
3. รัน `djlint APP01/templates/` เพื่อตรวจ template
4. สร้าง Pull Request → assign reviewer
5. Squash merge เมื่อผ่าน review

---

*Generated from codebase analysis — ส่วน TODO ยังรอการเติมเนื้อหา*
