# 📚 Library Service API

An online book rental service that allows users to borrow books, make payments, and receive notifications via Telegram. Includes admin features, JWT authentication, and background tasks for overdue monitoring.

## 📌 Features

- 📖 Book rental system with availability tracking
- 💳 Payment integration via Stripe (simplified checkout)
- 🕐 Overdue tracking and daily reminders using Django Q and Redis
- 📨 Telegram notifications to admin on new borrowings and overdue cases
- 🔐 JWT authentication (login via email)
- 🧑‍ Role-based access (Admin / User)
- 🛠️ Admin panel for management
- 📃 API documentation with Swagger (drf-spectacular)
- 🐳 Docker-based deployment

##  ⚙️️ Technologies Used

- Python, Django, Django REST Framework
- PostgreSQL
- Redis
- Docker, Docker Compose
- Django Q (task queue)
- python-telegram-bot (v13.15)
- drf-spectacular for API schema / Swagger documentation

## 🐳 Setup with Docker

1. **Clone the repository**
```
git clone https://github.com/YBlck/library-service-api.git
cd library-service-api
```
2. **Create and configure .env file**
```bash
cp .env.sample .env
# Fill in the required variables (Stripe keys, Telegram token, DB config, etc.)
```
3. **Build and run containers**
```bash
docker-compose up --build
```
The following services will run:
* web – Main Django app
* qcluster – Django-Q worker
* db – PostgreSQL database
* redis – Redis for Django Q

4. **Create a superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```
Now the API is available at http://localhost:8000/ and admin panel at http://localhost:8000/admin/.

5. **(Optional) Add a pre-configured task schedule to check for overdue borrowings daily**
```bash
docker-compose exec web python manage.py schedule_tasks
# You can also manage it in the admin panel
```

## 📦 Main Models
* **User** – Custom user model with email login
* **Book** – Books with title, author, inventory, and daily fee
* **Borrowing** – Links user to rented book and manages return/penalties
* **Payment** – Stripe session information for borrowings and fines

## 📂 Project Structure
```text
├── books/               # Book model & logic
├── borrowings/          # Borrowing logic
├── payments/            # Stripe integration
├── users/               # Custom user model
├── notifications/       # Telegram bot logic
├── library_service/     # Core settings & URLs
├── manage.py
├── docker-compose.yml
├── Dockerfile
└── .env.sample
```

## 🔐 Authentication
Authentication is done via JWT. Users register and log in using their email.

To get tokens, visit:
```
http://localhost:8000/api/users/token/ 
```

## 💳 Stripe Integration
* Stripe session is automatically created when a borrowing is made.
* User is redirected to Stripe's hosted checkout via success URL.
* No webhooks are used for simplicity.
* If a book is returned late, a penalty payment is automatically generated.

## 🔁 Book Return Logic
* Send a POST request to /api/borrowings/<id>/return/
* If the return is not overdue, it is processed instantly.
* If overdue, a fine payment is created and must be paid.

## 🔔 Notifications
* On new borrowings, a Telegram message is sent to the admin chat.
* Daily scheduled task checks for overdue books and notifies admin.
* Notifications are powered by python-telegram-bot.

## 📃 API Documentation
After running the app to see full API documentation visit:
```
http://localhost:8000/api/doc/swagger/
```
## 🧪 Running Tests

To run the tests with coverage, use the following commands:
```bash
docker-compose exec web coverage run manage.py test
```
To view the test coverage report:
```bash
docker-compose exec web coverage report
```