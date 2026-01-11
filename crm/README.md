# CRM Celery Setup and Usage

This document outlines the steps to set up and run Celery with Redis for the CRM application, including how to start the Celery worker and Celery Beat for scheduled tasks, and how to verify the generated reports.

## Prerequisites

-   **Redis:** Celery uses Redis as a message broker. Ensure Redis is installed and running on your system.
    -   **Installation (Ubuntu/Debian):**
        ```bash
        sudo apt update
        sudo apt install redis-server
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
        ```
    -   **Installation (macOS via Homebrew):**
        ```bash
        brew install redis
        brew services start redis
        ```
    -   **Verification:**
        ```bash
        redis-cli ping
        # Expected output: PONG
        ```

## Setup Steps

1.  **Install Python Dependencies:**
    Ensure all required Python packages, including `celery`, `django-celery-beat`, and `redis`, are installed.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Django Migrations:**
    Apply any pending database migrations for the Django project.
    ```bash
    python manage.py migrate
    ```

3.  **Start Celery Worker:**
    The Celery worker executes the tasks. Open a new terminal and run:
    ```bash
    celery -A alx_backend_graphql_crm worker -l info
    ```
    *   `-A alx_backend_graphql_crm`: Specifies the Celery application instance.
    *   `worker`: Starts the worker process.
    *   `-l info`: Sets the logging level to info, providing detailed output.

4.  **Start Celery Beat Scheduler:**
    Celery Beat is the scheduler that triggers periodic tasks (like the CRM report generation). Open another new terminal and run:
    ```bash
    celery -A alx_backend_graphql_crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ```
    *   `beat`: Starts the beat scheduler process.
    *   `--scheduler django_celery_beat.schedulers:DatabaseScheduler`: Specifies Django's database scheduler, which allows managing schedules via the Django admin.

## Verification

After starting the Celery worker and beat, the `generate_crm_report` task is scheduled to run weekly (every Monday at 06:00 UTC by default, as configured in `settings.py`).

To verify that the report is being generated:

1.  **Check the log file:**
    The CRM reports will be appended to the `/tmp/crm_report_log.txt` file.
    ```bash
    cat /tmp/crm_report_log.txt
    ```
    You should see entries similar to:
    `YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, Z revenue`

2.  **Manually Triggering a Task (for testing purposes):**
    You can manually trigger the `generate_crm_report` task from a Django shell to test its functionality immediately without waiting for the scheduled time:
    ```bash
    python manage.py shell
    ```
    ```python
    from crm.tasks import generate_crm_report
    generate_crm_report.delay()
    ```
    Then, check `/tmp/crm_report_log.txt` again.