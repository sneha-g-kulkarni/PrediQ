# PrediQ - Exam Preparation Web Application

PrediQ is a comprehensive web-based exam preparation platform for 10th and 2nd PU students. It provides access to previous year question papers, AI-powered practice paper generation, and semantic analysis of questions.

## Features

### Student Features
- **Previous Year Papers**: Browse and download question papers by year, board, course, and subject
- **AI Practice Generation**: Generate custom practice papers with selectable difficulty levels (Easy/Medium/Hard)
- **Semantic Analysis**: AI analyzes question patterns and difficulty using NLP
- **Free Downloads**: 2 free downloads per student
- **Payment System**: Mock payment interface (₹40 for additional access)
- **Download History**: Track all paper downloads

### Admin Features
- **Upload Question Papers**: Add new papers with PDF file upload
- **View All Papers**: Manage question paper database
- **Payment Tracking**: Monitor all student transactions
- **Download Analytics**: View download activity logs
- **Dashboard Statistics**: Overview of papers, payments, and downloads

## Technology Stack

- **Backend**: Flask 3.0.0, Python 3.8+
- **Frontend**: Bootstrap 5.3.0, Jinja2 templates, Font Awesome icons
- **Database**: SQLite3
- **NLP**: NLTK, scikit-learn (TF-IDF vectorization)
- **PDF Processing**: PyPDF2, ReportLab, FPDF2
- **Authentication**: Flask-Login with session management
- **Security**: SHA-256 password hashing

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Navigate to project directory**
   ```bash
   cd C:\Users\hp\Desktop\PrediQ
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download NLTK data** (first run only)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

4. **Run the web application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

## Default Credentials

### Admin Login
- Username: `admin`
- Password: `admin123`

### Student Registration
Register new student accounts via the registration page.

## Project Structure

```
PrediQ/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── src/
│   ├── config.py              # Configuration constants
│   ├── database/
│   │   └── db_manager.py      # Database operations
│   ├── nlp/
│   │   └── semantic_analyzer.py  # NLP question analysis
│   └── utils/
│       └── pdf_manager.py     # PDF processing
├── templates/                  # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── student/              # Student pages
│   └── admin/                # Admin pages
└── static/
    ├── css/
    │   └── style.css         # Custom styling
    └── js/
        └── main.js           # Client-side JavaScript
```

## Database Schema

### Tables
- **users**: Student accounts with free download tracking
- **admin**: Administrator accounts
- **question_papers**: Uploaded question papers metadata
- **questions**: Individual questions extracted from papers
- **payments**: Payment transaction records
- **downloads**: Download activity logs
- **Database**: SQLite
- **NLP**: NLTK, scikit-learn
- **PDF Processing**: PyPDF2, ReportLab, FPDF

## Author
PrediQ Development Team