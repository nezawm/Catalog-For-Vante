# VanteCTL

A bilingual (Persian / English) product catalog built with Django, featuring a dedicated Persian-language management panel for non-technical clients.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Django](https://img.shields.io/badge/Django-6.1-092E20)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)

<!-- Replace with a real screenshot after uploading it to docs/screenshots/ -->
<!-- ![Home page](docs/screenshots/home.png) -->

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Client Panel](#client-panel)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [License](#license)

## Features

- **Hierarchical catalog**: categories, subcategories, and products with configurable display order.
- **Bilingual content**: every title, name, and description has a Persian and an English version; visitors choose their language on the landing page.
- **Client management panel** at `/panel/`: a simple, always-Persian interface for creating, editing, and deleting categories, subcategories, and products, with no need to use the Django admin.
- **Automatic slugs**: URL-friendly slugs are generated from names, with a live preview in the panel and admin.
- **Role-based access**: a dedicated `Catalog Manager` group limits panel users to catalog permissions only. It is created automatically after `migrate`.
- **Configuration via environment variables**: `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` are read from the environment (or a `.env` file); the app refuses to start in production without them.
- **Vanlite rows**: the Vanlite table on a product page is edited in the panel's product form and shown on the site from the same rows.

## Screenshots

Add screenshots to `docs/screenshots/` and reference them here:

| Home | Product detail | Client panel |
| --- | --- | --- |
| ![Home](docs/screenshots/home.png) | ![Product](docs/screenshots/product.png) | ![Panel](docs/screenshots/panel.png) |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.13 |
| Framework | Django 6.1 |
| Database | SQLite (default) |
| Configuration | Environment variables / `.env` file (small built-in loader) |
| Front end | Django templates, vanilla CSS and JavaScript |

## Project Structure

```
VanteCTL/
├── VanteCTL/      # Project settings, root URLs, WSGI/ASGI
├── Core/          # Landing page, language selection, shared helpers
├── Category/      # Category and Subcategory models and public views
├── Product/       # Product model and public views
├── Panel/         # Client management panel (views/ is split by area: products, catalog, stats, users, ...)
├── templates/     # HTML templates, grouped by app
├── static/        # CSS, JavaScript, and images
├── .env.example   # Template for environment variables
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.13 or newer
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/VanteCTL.git
cd VanteCTL

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file and edit the values
cp .env.example .env             # Windows: copy .env.example .env

# 5. Create the database and an admin user
python manage.py migrate
python manage.py createsuperuser
python manage.py create_panel_client <username>   # panel user for the client

# 6. Start the development server
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser. The Django admin is available at `/admin/`.

## Configuration

Settings are read from real environment variables or from a `.env` file next to `manage.py` (real environment variables win). Copy `.env.example` to `.env` and adjust it. `.env` is git-ignored.

| Variable | Description | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Secret key. **Required** when `DJANGO_DEBUG` is off; the app will not start without it. | none (a dev-only key is used when `DJANGO_DEBUG=True` and in tests) |
| `DJANGO_DEBUG` | Debug mode (`True` / `False`). Keep it `False` on a server. | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. **Required** when debug is off. | `localhost,127.0.0.1` in debug |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Optional, e.g. `https://example.com`. | empty |
| `DJANGO_HTTPS` | Optional. Only when the site really runs on https: secure cookies, redirect to https, HSTS. | `False` |
| `DJANGO_BEHIND_PROXY` | Optional. Behind a proxy that sends `X-Forwarded-Proto`. | `False` |
| `LOG_TRUST_PROXY_HEADER` | Optional. Trust `X-Forwarded-For` for visitor IPs. | `False` |

To generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### Leaked key

An earlier version of `settings.py` contained a hard-coded `SECRET_KEY`. That key is public in the git history and is rejected by the app when `DJANGO_DEBUG` is off. If it was ever used on a server, generate a new one and set it only on the server. Removing it from the file is not enough, because it stays in the history.

## Client Panel

The panel at `/panel/` is intended for the site owner or client. It is always shown in Persian, regardless of the site language.

Create a panel user from the command line:

```bash
python manage.py create_panel_client <username>
```

You will be prompted for a password. Alternatively, create a user in the Django admin and add them to the **Catalog Manager** group.

Panel users can view, add, change, and delete categories, subcategories, and products, and nothing else.

## Running Tests

```bash
python manage.py test
```

## Deployment

1. Set `DJANGO_DEBUG=False`, a new `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` (and `DJANGO_CSRF_TRUSTED_ORIGINS` for https) on the server.
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput` (written to `staticfiles/`)
4. Run the app with a production WSGI server (for example Gunicorn, installed separately) behind Nginx.
5. Nginx must serve `/static/` from `staticfiles/` and `/media/` from `media/`; Django does not serve them when debug is off.
6. Back up `db.sqlite3` and `media/` regularly, or move to a production database such as PostgreSQL.

> `.env` and `db.sqlite3` are intentionally excluded from version control. Never commit secrets or user data.

## License

No license has been specified yet. Add a `LICENSE` file to define how others may use this project.
