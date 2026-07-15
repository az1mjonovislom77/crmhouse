# CRM House

## Project Overview

CRM House is a comprehensive Customer Relationship Management (CRM) system designed to manage client interactions, sales processes, and project information for a real estate or construction company. This system aims to streamline operations, improve customer service, and enhance overall business efficiency. It includes a web interface for administration and management, as well as a Telegram bot for quick interactions and notifications.

## Features

*   **Client Management**: Track and manage customer information, leads, and communication history.
*   **Project Management**: Oversee various construction or real estate projects, including stages, deadlines, and associated clients.
*   **Booking Management**: Handle property bookings and reservations.
*   **Sales & Deals Tracking**: Monitor sales pipelines, deal statuses, and performance.
*   **Task Management**: Assign and track tasks related to clients, projects, and sales.
*   **Telegram Bot Integration**: Provide quick access to information, notifications, and basic interactions via a Telegram bot.
*   **Internationalization**: Support for multiple languages in the administrative interface.
*   **API Endpoints**: Robust RESTful API for integration with other services and mobile applications.
*   **Admin Panel**: Enhanced Django Admin interface for easy data management.
*   **Reporting**: Generate reports (e.g., Excel, Word) for various business metrics.
*   **Authentication**: Secure user authentication using JWT.

## Technologies Used

The project is built using modern web technologies and best practices:

*   **Backend**:
    *   Python 3.x
    *   [Django](https://www.djangoproject.com/): High-level Python Web framework.
    *   [Django REST Framework (DRF)](https://www.django-rest-framework.org/): Powerful and flexible toolkit for building Web APIs.
    *   [Celery](https://docs.celeryq.dev/en/stable/): Asynchronous task queue/job queue based on distributed message passing.
    *   [Redis](https://redis.io/): In-memory data structure store, used as a message broker for Celery and caching.
    *   [Gunicorn](https://gunicorn.org/): Python WSGI HTTP Server for UNIX.
    *   [djangorestframework-simplejwt](https://pypi.org/project/djangorestframework-simplejwt/): JWT authentication for DRF.
    *   [django-modeltranslation](https://django-modeltranslation.readthedocs.io/en/latest/): Translate model fields in Django.
    *   [django-jazzmin](https://django-jazzmin.readthedocs.io/): Jazzy and configurable Django admin.
    *   [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/): API documentation generation (OpenAPI/Swagger).
    *   [django-cors-headers](https://pypi.org/project/django-cors-headers/): Handles Cross-Origin Resource Sharing (CORS).
    *   [Pillow](https://python-pillow.org/): Image processing library.
    *   [openpyxl](https://openpyxl.readthedocs.io/en/stable/) / [python-docx](https://python-docx.readthedocs.io/en/latest/): Libraries for reading/writing Excel and Word files.
    *   [pandas](https://pandas.pydata.org/): Data analysis and manipulation tool.

*   **Telegram Bot**:
    *   [aiogram](https://docs.aiogram.dev/en/latest/): Asynchronous Telegram Bot API framework for Python.

## Installation

To set up the project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/az1mjonovislom77/crm_house.git
    cd crm_house
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the `config` directory (or project root, depending on your `python-decouple` setup) and add your environment-specific variables.
    Example `.env`:
    ```
    SECRET_KEY=your_django_secret_key
    DEBUG=True
    DATABASE_URL=postgres://user:password@host:port/dbname
    REDIS_URL=redis://localhost:.../0
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    ```

5.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser (for Django Admin access):**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

8.  **Start Celery worker (in a separate terminal):**
    ```bash
    celery -A config worker -l info
    ```

9.  **Start Celery Beat (for scheduled tasks, in another separate terminal):**
    ```bash
    celery -A config beat -l info
    ```

10. **Run the Telegram Bot (if applicable, in another separate terminal):**
    (You might need to locate the main bot script, e.g., `python instagram/bot.py` or similar, depending on your project structure)

The web application will be accessible at `http://127.0.0.1:8000/`.
The Django Admin panel will be at `http://127.0.0.1:8000/admin/`.
API documentation (Swagger UI) will be at `http://127.0.0.1:8000/swagger/` or `http://127.0.0.1:8000/redoc/`.

## Usage

*   **Web Interface**: Access the Django Admin panel to manage clients, projects, bookings, and other data.
*   **API**: Utilize the RESTful API for programmatic access to the CRM functionalities. Refer to the API documentation (`/swagger/` or `/redoc/`) for available endpoints and schemas.
*   **Telegram Bot**: Interact with the Telegram bot for quick queries, notifications, or specific actions (e.g., `/status`, `/new_lead`).

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

