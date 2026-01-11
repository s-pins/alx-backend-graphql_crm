# CRM Application - Celery and Cron Job Setup

This document provides instructions on how to set up and run the background tasks for the CRM application, which include Celery-based reporting and `django-crontab` jobs.

## 1. Prerequisites

### Install Redis
Celery requires a message broker to handle communication between the web application and the workers. We use Redis for this.

**On Debian/Ubuntu:**
```sh
sudo apt-get update
sudo apt-get install redis-server
```

**On macOS (using Homebrew):**
```sh
brew install redis
brew services start redis
```

Verify that Redis is running:
```sh
redis-cli ping
# Expected output: PONG
```

### Install Python Dependencies
Install all required Python packages from `requirements.txt`:
```sh
pip install -r requirements.txt
```

## 2. Database Migrations
The `django-celery-beat` library adds its own database models to store task schedules. You need to run migrations to create the necessary tables.

```sh
python manage.py migrate
```

## 3. Running Background Services
To run the automated tasks, you need to start two separate services: a Celery worker and the Celery Beat scheduler. It's recommended to run each command in a separate terminal window.

### Start the Celery Worker
The worker is the process that executes the tasks. It listens for jobs from the Redis message queue.

```sh
# The project name 'alx_backend_graphql' should be used with the -A flag.
celery -A alx_backend_graphql worker -l info
```
You should see the worker connect and list the discovered tasks, including `crm.tasks.generate_crm_report`.

### Start the Celery Beat Scheduler
Celery Beat is the scheduler. It's responsible for sending tasks to the queue at their scheduled time (e.g., the weekly report).

```sh
# The project name 'alx_backend_graphql' should be used with the -A flag.
celery -A alx_backend_graphql beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
This will start the scheduler, which will periodically check for tasks that need to be run.

## 4. Verifying Task Execution
The Celery tasks and cron jobs are configured to write to log files in the `/tmp/` directory.

- **Weekly CRM Report (Celery):**
  Check the contents of this file after the scheduled time (Monday at 6:00 AM UTC).
  ```sh
  tail -f /tmp/crm_report_log.txt
  ```
  *Expected output:* `YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, Z.ZZ revenue`

- **Heartbeat Log (`django-crontab`):**
  This log should be updated every 5 minutes.
  ```sh
  tail -f /tmp/crm_heartbeat_log.txt
  ```

- **Low Stock Updates (`django-crontab`):**
  This log is updated every 12 hours.
  ```sh
  tail -f /tmp/low_stock_updates_log.txt
  ```
- **Order Reminders (`cron`):**
  This log is updated daily at 8:00 AM.
  ```sh
  tail -f /tmp/order_reminders_log.txt
  ```
- **Customer Cleanup (`cron`):**
  This log is updated every Sunday at 2:00 AM.
  ```sh
  tail -f /tmp/customer_cleanup_log.txt
  ```

## 5. Running django-crontab jobs
To install the cronjobs defined in settings.py into user's crontab run the following command
```sh
python manage.py crontab add
```
To view active cronjobs
```sh
python manage.py crontab show
```
To remove cronjobs
```sh
python manage.py crontab remove
```
