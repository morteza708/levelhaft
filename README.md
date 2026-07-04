# LevelHaft | لول هفت

[![Live Demo](https://img.shields.io/badge/Live-levelhaft.com-28a745?style=flat-square)](https://levelhaft.com)
[![License](https://img.shields.io/badge/License-Source%20Available-red?style=flat-square)](LICENSE)
[![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

**A production-grade Persian (RTL) e-commerce platform for skincare & beauty products.**

| | |
|---|---|
| **Live** | [https://levelhaft.com](https://levelhaft.com) |
| **Author** | [Morteza Kamalian](https://kamalian.dev/en) |
| **Portfolio** | [github.com/morteza708/portfolio](https://github.com/morteza708/portfolio) |

---

## English

### Overview

**LevelHaft** is a full-stack e-commerce web application built for a real skincare retail business in Iran. The platform supports OTP-based authentication, beautician-tier pricing, online payments, an internal wallet, admin import/export, background SMS jobs, and PWA installation on mobile devices.

Deployed on **Liara** with **PostgreSQL** in production.

### Key Features

#### Authentication & Users
- Phone number login/register with OTP (Kavenegar SMS API)
- User profiles with beautician verification (admin approval + SMS notification)
- Role-based pricing: regular customers vs. verified beauticians

#### Catalog & Shopping
- Multi-level taxonomy: brand → line → product
- Unique barcode, multiple images, rich text descriptions (CKEditor 5)
- Dual price levels, stock management, out-of-stock badges on product cards
- Product search, skin-consult recommendation flow, accessories listing
- Shopping cart with session/user persistence

#### Orders & Payments
- Order lifecycle management
- **Pasargad (PEP)** payment gateway integration
- Internal wallet for future purchases
- Printable admin order invoice (HTML → browser PDF)

#### Admin Panel
- Safe CSV/XLSX **export** for users, profiles, products, orders, workshops
- Controlled **import/update** by barcode (products) and mobile (profiles)
- Superuser-only user import; B2B discount reports export-only
- Order autocomplete fields, read-only order line item inlines

#### Content & Community
- Blog with categories
- Product comments (login required) with admin moderation + star ratings
- Workshop registration with SMS confirmation on approval
- Business discount reporting for B2B partners

#### Performance & UX
- Query optimization with `select_related` / `prefetch_related`
- Persian digit normalization, Jalali date support (`django-jalali`)
- Responsive RTL UI (Bootstrap 5)
- PWA support (installable on mobile)
- Compact mobile pagination for search results

### Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3 |
| Framework | Django 5 |
| Database | PostgreSQL |
| SMS | Kavenegar API |
| Payments | Pasargad (PEP) |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| Rich text | django-ckeditor-5 |
| Admin tools | django-import-export, openpyxl |
| Static files | WhiteNoise |
| Deploy | Liara (PaaS) |

### Project Structure

```
LevelHaft_main/
├── accounts/            # OTP auth, profiles, beautician requests
├── products/            # Catalog, search, consult, comments
├── cart/                # Shopping cart
├── orders/              # Orders, payments, admin invoice
├── wallet/              # Internal wallet
├── business_discounts/    # B2B discount codes & reports
├── workshop/            # Workshop registrations
├── blogs/               # Blog posts
├── pages/               # Static pages
├── gateways/            # Payment gateway (Pasargad)
├── config/              # Settings, import/export utilities
├── templates/           # HTML templates (RTL)
├── static/              # CSS, JS, images
├── requirements.txt
├── .env.example
└── LICENSE
```

### Local Development

**Prerequisites:** Python 3.10+, PostgreSQL

```bash
git clone https://github.com/morteza708/LevelHaft_main.git
cd LevelHaft_main

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your local values — NEVER commit this file

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Collect static files (production-like local test):

```bash
python manage.py collectstatic --noinput
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | `True` for local dev only |
| `DATABASE_URL` | PostgreSQL URL (production / Liara) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Local DB fallback |
| `KAVENEGAR_API` | Kavenegar SMS API key |
| `PEP_USERNAME`, `PEP_PASSWORD`, `PEP_TERMINAL_NO` | Pasargad payment gateway |
| `SITE_URL` | Public site URL |
| `ADMIN_PHONE` | Admin phone for notifications |

See [`.env.example`](.env.example) for the full template.

### Security Notes (public repository)

- Never commit `.env`, API keys, or database dumps
- `media/` and `staticfiles/` must not be in the repository
- If secrets were ever committed to git history, run `git filter-repo` before going public

### License

**Source Available** — see [LICENSE](LICENSE).

Published for **portfolio review and learning**. Commercial use, redistribution, deployment, or derivative works require **written permission** from the author.

---

## فارسی

### معرفی

**لول هفت (LevelHaft)** یک فروشگاه اینترنتی فارسی (RTL) برای محصولات مراقبت از پوست است که در محیط production روی **لیارا** با **PostgreSQL** اجرا می‌شود.

شامل احراز هویت OTP، سطح‌بندی بیوتیشن، پرداخت آنلاین، کیف پول داخلی، import/export امن در پنل ادمین، فاکتور PDF سفارش، PWA و بهینه‌سازی Query است.

### ویژگی‌های کلیدی

- ورود و ثبت‌نام با OTP (کاوه‌نگار)
- پروفایل و تایید بیوتیشن توسط ادمین
- کاتالوگ چندسطحی با بارکد و دو سطح قیمت
- سبد خرید، سفارش، درگاه پاسارگاد (PEP)، کیف پول
- نمایش «ناموجود» روی کارت محصول
- ادمین: export/import امن، فاکتور سفارش
- وبلاگ، کامنت، ورکشاپ، تخفیفات سازمانی
- pagination فشرده موبایل برای نتایج جستجو

### نصب محلی

```bash
git clone https://github.com/morteza708/LevelHaft_main.git
cd LevelHaft_main
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### لینک‌ها

| | |
|---|---|
| **سایت** | [levelhaft.com](https://levelhaft.com) |
| **نویسنده** | [kamalian.dev](https://kamalian.dev/en) |
| **Portfolio** | [github.com/morteza708/portfolio](https://github.com/morteza708/portfolio) |

### لایسنس

کد به صورت **Source Available** منتشر شده است. مشاهده برای portfolio مجاز است. استفاده تجاری، کپی، deploy مجدد یا ساخت نسخه مشتق **بدون اجازه کتبی** مجاز نیست. جزئیات در [LICENSE](LICENSE).

---

<p align="center">
  Built with care by <a href="https://kamalian.dev/en">Morteza Kamalian</a>
</p>
