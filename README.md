# Jazan Kitchen Project

A Django web application developed as a course project.  
The system simulates a simple online store that allows users to browse products, contact the store, and complete a checkout process with invoice generation.

## Features

- Product listing page
- Product detail page
- Checkout system
- Contact form with database storage
- Email confirmation after submitting a message
- User profile page
- Invoice generation with QR code
- Django Admin panel for product management

## Technologies Used

- Python
- Django
- HTML / CSS
- Bootstrap
- SQLite
- QR Code generation

## Project Structure
jazan_kitchen_project
│
├── core
├── shop
├── static
├── manage.py
└── requirements.txt

## Installation

1. Clone the repository
git clone https://github.com/Mohammed-Maashi/jazan_kitchen_project.git

2. Navigate to the project folder
cd jazan_kitchen_project

3. Install dependencies
pip install -r requirements.txt

4. Run migrations
python manage.py migrate

5. Run the development server
python manage.py runserver

6. Open in browser
http://127.0.0.1:8000

## Author

Course project developed for Django Framework class.
