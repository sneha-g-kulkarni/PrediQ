"""
Configuration settings for PrediQ Application
"""

import os

# Application settings
APP_NAME = "PrediQ"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Smart Exam Preparation System"

# Database settings
DATABASE_NAME = "prediq.db"

# Default admin credentials
DEFAULT_ADMIN = {
    'email': 'admin@prediq.com',
    'password': 'admin123',
    'name': 'PrediQ Administrator'
}

# File upload settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.pdf']

# Download settings
FREE_DOWNLOADS_LIMIT = 2
PAID_DOWNLOAD_PRICE = 40.00  # INR

# Question paper settings
DEFAULT_QUESTIONS_PER_PAPER = 20
SIMILARITY_THRESHOLD = 0.7

# Difficulty distribution (percentages)
DIFFICULTY_DISTRIBUTION = {
    'easy': {
        'easy': 0.8,
        'medium': 0.2,
        'hard': 0.0
    },
    'medium': {
        'easy': 0.4,
        'medium': 0.4,
        'hard': 0.2
    },
    'hard': {
        'easy': 0.2,
        'medium': 0.3,
        'hard': 0.5
    }
}

# Subject configurations
SUBJECTS_CONFIG = {
    '10th': {
        'CBSE': ['Mathematics', 'Science', 'Social Science', 'English'],
        'STATE': ['Mathematics', 'Science', 'Social Science', 'English']
    },
    '2nd_PU': {
        'STATE': {
            'PCMB': ['Physics', 'Chemistry', 'Mathematics', 'Biology'],
            'PCMC': ['Physics', 'Chemistry', 'Mathematics', 'Computer Science']
        }
    }
}

# UI Theme colors
THEME_COLORS = {
    'primary': '#1e3a8a',      # Dark blue
    'secondary': '#000000',     # Black
    'background': '#ffffff',    # White
    'text_primary': '#000000',  # Black text
    'text_secondary': '#1e3a8a', # Blue text
    'accent': '#3b82f6',       # Light blue
    'button_hover': '#1e40af'   # Darker blue for hover
}

# Paths
def get_project_root():
    """Get the project root directory"""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def get_data_dir():
    """Get the data directory"""
    return os.path.join(get_project_root(), 'data')

def get_uploads_dir():
    """Get the uploads directory"""
    return os.path.join(get_project_root(), 'uploads')

def get_downloads_dir():
    """Get the downloads directory"""
    return os.path.join(get_project_root(), 'downloads')

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [get_data_dir(), get_uploads_dir(), get_downloads_dir()]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Application constants
class Constants:
    """Application constants"""
    
    # User types
    USER_TYPE_STUDENT = 'student'
    USER_TYPE_ADMIN = 'admin'
    
    # Question types
    QUESTION_TYPE_MCQ = 'MCQ'
    QUESTION_TYPE_SHORT = 'SHORT'
    QUESTION_TYPE_MEDIUM = 'MEDIUM'
    QUESTION_TYPE_LONG = 'LONG'
    
    # Difficulty levels
    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_MEDIUM = 'medium'
    DIFFICULTY_HARD = 'hard'
    
    # Download types
    DOWNLOAD_TYPE_PREVIOUS_YEAR = 'PREVIOUS_YEAR'
    DOWNLOAD_TYPE_GENERATED_PAPER = 'GENERATED_PAPER'
    
    # Payment status
    PAYMENT_STATUS_SUCCESS = 'SUCCESS'
    PAYMENT_STATUS_FAILED = 'FAILED'
    PAYMENT_STATUS_PENDING = 'PENDING'
    
    # Boards
    BOARD_CBSE = 'CBSE'
    BOARD_STATE = 'STATE'
    
    # Courses
    COURSE_PCMB = 'PCMB'
    COURSE_PCMC = 'PCMC'
    
    # Class levels
    CLASS_10TH = '10th'
    CLASS_2ND_PU = '2nd_PU'