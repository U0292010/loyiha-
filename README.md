# UyTop

UyTop uy-joy e'lonlari platformasi uchun Django loyihasi.

## Bosqichlar

### 1-bosqich: Django setup

Talablar: Python 3.12 yoki undan yangi versiya.

PowerShell'da loyiha papkasidan:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Python launcher (`py`) mavjud bo'lmasa, virtual muhitni `python -m venv .venv` bilan yarating.
Brauzerda http://127.0.0.1:8000/admin/ manzilini ochib, `createsuperuser` buyrug'ida yaratgan hisobingiz bilan kiring.

Mahalliy muhit `.env` faylidan sozlanadi. U Git'ga qo'shilmaydi; deploy vaqtida `SECRET_KEY` qiymatini maxfiy muhit o'zgaruvchisi bilan almashtiring.

`DATABASE_URL` berilmagan bo'lsa, lokal ishlab chiqishda SQLite ishlatiladi.

### 2-bosqich: Modellar va database

`properties` ilovasida `Profile`, `Property`, `PropertyImage` va `Favorite` modellari mavjud.
PostgreSQL ishlatish uchun PostgreSQL serverida `uytop` bazasini yarating, `.env` fayliga
quyidagini qo'shing va qiymatlarni muhitga moslang:

```dotenv
DATABASE_URL=postgresql://uytop:parol@127.0.0.1:5432/uytop
```

So'ng migratsiyalarni yarating va qo'llang:

```powershell
python manage.py migrate
python manage.py check
python manage.py test properties
```

`properties/migrations/0001_initial.py` migratsiyasi loyihaga qo'shilgan. Yangi model o'zgarishlaridan keyin `python manage.py makemigrations` bilan navbatdagi migratsiyani yarating.

### 3-bosqich: Admin

Django admin orqali foydalanuvchilarni boshqarish mumkin. `properties` adminida e'lonlarni qidirish va filterlash, holatini bulk tarzda tasdiqlash/rad etish/kutilmoqda holatiga qaytarish, shuningdek e'lon rasmlarini inline boshqarish mavjud. Profile, rasm va favorite yozuvlari uchun alohida admin ro'yxatlari ham qo'shilgan.

```powershell
python manage.py createsuperuser
python manage.py runserver
```

`http://127.0.0.1:8000/admin/` manziliga superuser bilan kiring. Admin tekshiruvlari:

```powershell
python manage.py test properties
```

### 4-bosqich: Authentication

Ro'yxatdan o'tish, login, POST orqali logout va login bilan himoyalangan profilni yangilash:

```powershell
python manage.py runserver
```

Sahifalar: `/register/`, `/login/`, `/logout/`, `/profile/`. Profile sahifasi user ismi, familiyasi, emaili, telefon raqami, bio va profil rasmini yangilaydi. Auth oqimi testlari:

```powershell
python manage.py test accounts
```

### 5-bosqich: Home va UI

Bosh sahifa `/` manzilida tasdiqlangan, yangi va admin tanlagan tavsiya e'lonlarini ko'rsatadi. Admin paneldagi e'lonlar ro'yxatidan `is_featured` belgisini o'zgartirib tavsiya blokini boshqaring. Bosh sahifadagi qidiruv 7-bosqichdagi umumiy e'lonlar ro'yxatiga olib boradi.

```powershell
python manage.py makemigrations properties
python manage.py migrate
python manage.py test
python manage.py runserver
```

Mavjud e'lonlarning `is_featured` qiymati migration'dan so'ng `False` bo'ladi; admin'dan tavsiya sifatida belgilang. Property kartalaridagi to'liq sahifaga o'tish va CRUD 6-bosqichda ulanadi.

### 6-bosqich: Property CRUD

Kirish qilgan foydalanuvchi e'lon yaratishi, o'z e'lonini tahrirlashi yoki o'chirishi mumkin. E'lon yaratish va tahrirlashda 10 tagacha tekshirilgan rasm yuklash hamda mavjud rasmlarni o'chirish mumkin. Har bir yangi yoki tahrirlangan e'lon moderatsiyaga `PENDING` holatida boradi. Ommaga faqat `APPROVED` e'lonlar ko'rinadi; egasi va staff o'z holati qanday bo'lishidan qat'i nazar ko'ra oladi.

```powershell
python manage.py test properties
python manage.py runserver
```

Route'lar: `/properties/create/`, `/properties/<slug>/`, `/properties/<slug>/edit/`, `/properties/<slug>/delete/`. Rasm hajmi har biri 10 MB bilan cheklangan.

### 7-bosqich: Search va filter

E'lonlar `/properties/` sahifasida qidiriladi. Sotish va ijara uchun `/properties/sale/`, `/properties/rent/` route'lari mavjud. Kalit so'z, e'lon turi, uy turi, shahar, tuman, narx va maydon oralig'i, xonalar soni bo'yicha filterlash; eng yangi/narx/maydon bo'yicha saralash va sahifalash qo'shilgan. Faqat tasdiqlangan e'lonlar natijalarga kiradi.

```powershell
python manage.py test properties
python manage.py runserver
```

### 8-bosqich: Favorites

Kirish qilgan foydalanuvchi tasdiqlangan e'lonlarni kartadagi yurak orqali saqlaydi yoki olib tashlaydi. Saqlangan e'lonlar `/favorites/` sahifasida va profil havolasida ko'rinadi; toggle so'rovi faqat POST orqali bajariladi.

```powershell
python manage.py test favorites
```

### 9-bosqich: Admin approval

Admin bulk action'lari e'lonni tasdiqlaydi, rad etadi yoki qayta ko'rib chiqishga yuboradi. Moderatsiya natijasi `reviewed_by` va `reviewed_at` bilan qayd etiladi; rad etish sababi admin formida yoziladi va e'lon egasiga ko'rinadi. Foydalanuvchi tahrir qilgan e'lon qayta `PENDING` holatiga o'tib, oldingi moderatsiya metama'lumotlari tozalanadi.

```powershell
python manage.py makemigrations properties
python manage.py migrate
python manage.py test properties
```

### 10-bosqich: Responsive va testing

Home, e'lonlar ro'yxati, detail, CRUD formalar, saqlanganlar va profil sahifalari 375 px, 768 px va 1280 px viewportlarda tekshirildi. Tekshiruvda gorizontal overflow aniqlanmadi. Testlar auth, moderation, e'lon CRUD/rasmlar, qidiruv filter/saralash/pagination va favorites oqimlarini qamrab oladi.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py runserver
```

Lokal interaktiv smoke-test uchun `http://127.0.0.1:8001/` ni oching; test qamrovi qo'shilganda yangi oqimni avval tegishli app bilan, so'ng to'liq `python manage.py test` bilan tekshiring.

### 11-bosqich: Docker va PostgreSQL

Talablar: Docker Desktop ishga tushgan bo'lsin. Compose ikki service ko'taradi: `web` (Gunicorn, WhiteNoise, migratsiyalar) va `db` (PostgreSQL 16). PostgreSQL ma'lumoti `postgres_data`, yuklangan rasmlar `media_data` nomli persistent volume'da saqlanadi. Mavjud `.env` faylingiz ustiga yozmang.

PowerShell'da, loyiha papkasida:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -c "import secrets; print(secrets.token_hex(24))"
```

Chiqqan maxfiy qiymatni `.env` dagi `POSTGRES_PASSWORD` o'rniga qo'ying. Bir xil qiymat `DATABASE_URL` ichida ham kerak bo'lsa, parol URL-safe hex ko'rinishida bo'lgani uchun qo'shimcha URL encoding talab qilinmaydi. `DATABASE_URL` berilmasa Compose uni `POSTGRES_*` qiymatlaridan tuzadi. Lokal dev default paroli production uchun yaramaydi; production `.env`ga `DEBUG=False` va yangi `SECRET_KEY` qo'ying.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs -f web
```

Brauzer: http://127.0.0.1:8000/ . Boshqa port kerak bo'lsa `.env`ga `WEB_PORT=8001` yozing. Birinchi ishga tushishda migratsiyalar va `collectstatic` container start vaqtida avtomatik bajariladi. Admin user yaratish va test:

```powershell
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

To'xtatish: `docker compose down`. Bu buyruq ma'lumot volume'larini saqlaydi. `docker compose down -v` ma'lumotlar bazasi va yuklangan rasmlarni o'chiradi, shuning uchun faqat ataylab tozalash kerak bo'lganda ishlating.# loyiha-
