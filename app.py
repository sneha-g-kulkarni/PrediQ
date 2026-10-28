"""
PrediQ Web Application
Flask-based web server for exam preparation system
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import sys
from datetime import datetime, timedelta
from functools import wraps

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.db_manager import DatabaseManager
from src.nlp.semantic_analyzer import SemanticAnalyzer
from src.utils.pdf_manager import PDFManager
from src.config import ensure_directories, get_uploads_dir, get_downloads_dir

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'prediq-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = get_uploads_dir()
app.config['DOWNLOAD_FOLDER'] = get_downloads_dir()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize managers
db_manager = DatabaseManager()
semantic_analyzer = SemanticAnalyzer()
pdf_manager = PDFManager()

# Ensure directories exist
ensure_directories()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, email, full_name, user_type):
        self.id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.user_type = user_type
    
    def is_admin(self):
        return self.user_type == 'admin'

@login_manager.user_loader
def load_user(user_id):
    """Load user from session"""
    user_type = session.get('user_type')
    
    if user_type == 'admin':
        result = db_manager.execute_query("SELECT * FROM admin WHERE id = ?", (user_id,))
        if result:
            row = result[0]
            return User(row['id'], row['email'], row['email'], row['full_name'], 'admin')
    else:
        result = db_manager.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if result:
            row = result[0]
            return User(row['id'], row['username'], row['email'], row['full_name'], 'student')
    return None

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'student')
        
        if user_type == 'admin':
            user_data = db_manager.authenticate_admin(username_or_email, password)
            if user_data:
                user = User(user_data['id'], user_data['email'], user_data['email'], 
                           user_data['full_name'], 'admin')
                login_user(user)
                session['user_type'] = 'admin'
                flash('Welcome back, Admin!', 'success')
                return redirect(url_for('admin_dashboard'))
        else:
            user_data = db_manager.authenticate_user(username_or_email, password)
            if user_data:
                user = User(user_data['id'], user_data['username'], user_data['email'],
                           user_data['full_name'], 'student')
                login_user(user)
                session['user_type'] = 'student'
                flash(f'Welcome back, {user_data["full_name"]}!', 'success')
                return redirect(url_for('student_dashboard'))
        
        flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Validation
        if not all([username, email, password, full_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        # Create user
        success = db_manager.create_user(username, email, password, full_name, phone)
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student dashboard"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get user statistics
    downloads_count = db_manager.get_user_downloads_count(current_user.id)
    download_stats = db_manager.get_user_download_stats(current_user.id)
    
    return render_template('student/dashboard.html',
                         downloads_count=downloads_count,
                         prev_year_downloads=download_stats['prev_year'],
                         practice_downloads=download_stats['practice'])

@app.route('/student/select', methods=['GET', 'POST'])
@login_required
def student_select():
    """Unified selection page - student selects criteria then chooses action"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        # Get selection criteria
        year = request.form.get('year')
        board = request.form.get('board', 'STATE')  # Default to STATE for 2nd PU
        course = request.form.get('course')
        subject = request.form.get('subject')
        
        if not all([year, subject]):
            flash('Please complete all selections.', 'warning')
            download_stats = db_manager.get_user_download_stats(current_user.id)
            return render_template('student/select.html',
                                 prev_year_downloads=download_stats['prev_year'],
                                 practice_downloads=download_stats['practice'])
        
        # Store selections in session
        session['year'] = year
        session['board'] = board
        session['course'] = course
        session['subject'] = subject
        
        # Directly generate frequency-sorted paper (main requirement)
        return redirect(url_for('generate_paper'))
    
    # GET request - show selection form
    download_stats = db_manager.get_user_download_stats(current_user.id)
    return render_template('student/select.html',
                         prev_year_downloads=download_stats['prev_year'],
                         practice_downloads=download_stats['practice'])

@app.route('/student/search-results', methods=['POST'])
@login_required
def search_results():
    """Display results page with two options after selection"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get selection criteria
    year = request.form.get('year')
    board = request.form.get('board', 'STATE')
    course = request.form.get('course')
    subject = request.form.get('subject')
    
    if not all([year, subject]):
        flash('Please complete all selections.', 'warning')
        return redirect(url_for('student_select'))
    
    # Store selections in session for later use
    session['year'] = year
    session['board'] = board
    session['course'] = course
    session['subject'] = subject
    
    # Get download stats
    download_stats = db_manager.get_user_download_stats(current_user.id)
    
    return render_template('student/results.html',
                         year=year,
                         board=board,
                         course=course,
                         subject=subject,
                         prev_year_downloads=download_stats['prev_year'],
                         practice_downloads=download_stats['practice'])

@app.route('/student/view-previous-year', methods=['POST'])
@login_required
def view_previous_year():
    """Generate and download previous year questions PDF"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get selections from form (sent from results page)
    year = request.form.get('year')
    board = request.form.get('board')
    course = request.form.get('course')
    subject = request.form.get('subject')
    
    if not all([year, subject]):
        flash('Please make your selections first.', 'warning')
        return redirect(url_for('student_select'))
    
    # Store in session
    session['year'] = year
    session['board'] = board
    session['course'] = course
    session['subject'] = subject
    
    # Check download limits (2 free, then ₹40 each)
    download_stats = db_manager.get_user_download_stats(current_user.id)
    total_downloads = download_stats['prev_year'] + download_stats['practice']
    needs_payment = total_downloads >= 2
    
    if needs_payment:
        # Store paper info for payment
        session['pending_paper_info'] = {
            'year': year,
            'board': board,
            'course': course,
            'subject': subject,
            'paper_type': 'PREVIOUS_YEAR'
        }
        return redirect(url_for('payment_required'))
    
    try:
        # Get all questions for this criteria from database
        class_level = "10th" if year == "10th" else "2nd_PU"
        all_questions = db_manager.get_questions_by_subject(subject, board, course, class_level)
        
        if not all_questions:
            flash('No questions found for the selected criteria. Please check with admin.', 'info')
            return redirect(url_for('student_select'))
        
        # Use semantic analyzer to group similar questions and count frequency
        grouped_questions = semantic_analyzer.group_similar_questions(all_questions)
        
        # Sort by frequency (descending - most asked first)
        sorted_groups = sorted(grouped_questions, key=lambda x: x['frequency'], reverse=True)
        
        # Generate PDF with sorted questions and year stamps on top-right
        pdf_filename = pdf_manager.generate_frequency_sorted_pdf(
            sorted_groups,
            subject,
            year,
            board,
            course
        )
        
        # Record download
        db_manager.add_download(
            user_id=current_user.id,
            download_type='PREVIOUS_YEAR',
            subject=subject,
            file_path=pdf_filename,
            is_free=(total_downloads < 2)
        )
        
        # Increment counter
        db_manager.increment_download_count(current_user.id, 'PREVIOUS_YEAR')
        
        # Redirect to download
        session['download_file'] = pdf_filename
        session['download_title'] = f"{subject} - Previous Year Questions (Sorted by Frequency)"
        return redirect(url_for('download_success'))
        
    except Exception as e:
        flash(f'Error generating paper: {str(e)}', 'danger')
        return redirect(url_for('student_select'))

@app.route('/student/generate-paper')
@login_required
def generate_paper():
    """Generate single PDF with ALL questions sorted by frequency with year stamps - MAIN FUNCTIONALITY"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get selections from session
    year = session.get('year')
    board = session.get('board')
    course = session.get('course')
    subject = session.get('subject')
    
    if not all([year, subject]):
        flash('Please make your selections first.', 'warning')
        return redirect(url_for('student_select'))
    
    # Check download limits (2 free, then ₹40 each)
    download_stats = db_manager.get_user_download_stats(current_user.id)
    total_downloads = download_stats['prev_year'] + download_stats['practice']
    needs_payment = total_downloads >= 2
    
    if needs_payment:
        # Store paper info for payment
        session['pending_paper_info'] = {
            'year': year,
            'board': board,
            'course': course,
            'subject': subject
        }
        return redirect(url_for('payment_required'))
    
    try:
        # Get all questions for this criteria from database
        class_level = "10th" if year == "10th" else "2nd_PU"
        all_questions = db_manager.get_questions_by_subject(subject, board, course, class_level)
        
        if not all_questions:
            flash('No questions found for the selected criteria. Please check with admin.', 'info')
            return redirect(url_for('student_select'))
        
        # Use semantic analyzer to group similar questions and count frequency
        grouped_questions = semantic_analyzer.group_similar_questions(all_questions)
        
        # Sort by frequency (descending - most asked first)
        sorted_groups = sorted(grouped_questions, key=lambda x: x['frequency'], reverse=True)
        
        # Generate PDF with sorted questions and year stamps on top-right
        pdf_filename = pdf_manager.generate_frequency_sorted_pdf(
            sorted_groups,
            subject,
            year,
            board,
            course
        )
        
        # Record download
        db_manager.add_download(
            user_id=current_user.id,
            download_type='PREVIOUS_YEAR',
            subject=subject,
            file_path=pdf_filename,
            is_free=(total_downloads < 2)
        )
        
        # Increment counter (use prev_year for all papers)
        db_manager.increment_download_count(current_user.id, 'PREVIOUS_YEAR')
        
        # Redirect to download
        session['download_file'] = pdf_filename
        session['download_title'] = f"{subject} - Previous Year Questions (Sorted by Frequency)"
        return redirect(url_for('download_success'))
        
    except Exception as e:
        flash(f'Error generating paper: {str(e)}', 'danger')
        return redirect(url_for('student_select'))

@app.route('/student/select-difficulty', methods=['GET', 'POST'])
@login_required
def select_difficulty():
    """Select difficulty level for practice paper generation"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get selections from form (if coming from results page) or session
    year = request.form.get('year') or session.get('year')
    board = request.form.get('board') or session.get('board')
    course = request.form.get('course') or session.get('course')
    subject = request.form.get('subject') or session.get('subject')
    
    # Store in session for later use
    if year and subject:
        session['year'] = year
        session['board'] = board
        session['course'] = course
        session['subject'] = subject
    
    if not all([year, subject]):
        flash('Please make your selections first.', 'warning')
        return redirect(url_for('student_select'))
    
    if request.method == 'POST':
        difficulty = request.form.get('difficulty')
        
        # If no difficulty selected, show difficulty selection page (coming from results page)
        if not difficulty:
            return render_template('student/difficulty.html',
                                 year=year,
                                 board=board,
                                 course=course,
                                 subject=subject)
        
        # Check download limits for practice papers
        download_stats = db_manager.get_user_download_stats(current_user.id)
        total_downloads = download_stats['prev_year'] + download_stats['practice']
        needs_payment = total_downloads >= 2
        
        if needs_payment:
            # Store paper info for payment
            session['pending_paper_info'] = {
                'year': year,
                'board': board,
                'course': course,
                'subject': subject,
                'paper_type': 'GENERATED_PAPER'
            }
            session['pending_difficulty'] = difficulty
            return redirect(url_for('payment_required'))
        
        try:
            # Get questions for generation
            class_level = "10th" if year == "10th" else "2nd_PU"
            all_questions = db_manager.get_questions_by_subject(subject, board, course, class_level)
            
            if not all_questions:
                flash('No questions found for the selected criteria. Please check with admin.', 'info')
                return redirect(url_for('student_select'))
            
            # Use semantic analyzer to process questions
            grouped_questions = semantic_analyzer.group_similar_questions(all_questions)
            
            # Sort by frequency for difficulty categorization
            sorted_groups = sorted(grouped_questions, key=lambda x: x['frequency'], reverse=True)
            
            # Categorize by difficulty
            from src.nlp.semantic_analyzer import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            categorized = analyzer.categorize_by_difficulty(sorted_groups)
            
            # Generate questions based on difficulty
            if difficulty == 'easy':
                # Most repeated questions
                selected_questions = categorized['easy'][:20]
            elif difficulty == 'medium':
                # Mix of repeated and moderate
                selected_questions = (
                    categorized['easy'][:10] +
                    categorized['medium'][:10]
                )
            else:  # hard
                # Mix with rare questions
                selected_questions = (
                    categorized['medium'][:10] +
                    categorized['hard'][:10]
                )
            
            # Generate PDF
            pdf_filename = pdf_manager.generate_practice_paper(
                selected_questions,
                subject,
                difficulty,
                year,
                board,
                course
            )
            
            # Record download
            db_manager.add_download(
                user_id=current_user.id,
                download_type='GENERATED_PAPER',
                subject=subject,
                difficulty=difficulty,
                file_path=pdf_filename,
                is_free=True
            )
            
            # Increment counter
            db_manager.increment_download_count(current_user.id, 'GENERATED_PAPER')
            
            # Redirect to download
            session['download_file'] = pdf_filename
            session['download_title'] = f"{subject} - Practice Paper ({difficulty.title()})"
            return redirect(url_for('download_success'))
            
        except Exception as e:
            flash(f'Error generating practice paper: {str(e)}', 'danger')
            return redirect(url_for('student_select'))
    
    # GET request - show difficulty selection
    return render_template('student/difficulty.html',
                         year=year,
                         board=board,
                         course=course,
                         subject=subject)

@app.route('/student/papers', methods=['GET', 'POST'])
@login_required
def student_papers():
    """View previous year papers"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        # Get selection
        year = request.form.get('year')
        board = request.form.get('board')
        course = request.form.get('course')
        subject = request.form.get('subject')
        
        if not all([year, subject]):
            flash('Please select year and subject.', 'warning')
            return render_template('student/papers.html', papers=[])
        
        # Get papers
        class_level = "10th" if year == "10th" else "2nd_PU"
        papers = db_manager.get_question_papers(board, subject, class_level)
        
        return render_template('student/papers.html', 
                             papers=papers,
                             selected_year=year,
                             selected_board=board,
                             selected_course=course,
                             selected_subject=subject)
    
    return render_template('student/papers.html', papers=[])

@app.route('/student/generate', methods=['GET', 'POST'])
@login_required
def student_generate():
    """Generate practice paper"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        # Get selection
        year = request.form.get('year')
        board = request.form.get('board')
        course = request.form.get('course')
        subject = request.form.get('subject')
        difficulty = request.form.get('difficulty', 'medium')
        
        if not all([year, subject]):
            flash('Please select year and subject.', 'warning')
            return render_template('student/generate.html')
        
        # Check download eligibility
        free_downloads_used = db_manager.get_user_free_downloads_used(current_user.id)
        if free_downloads_used >= 2:
            return redirect(url_for('payment_required'))
        
        try:
            # Get questions
            class_level = "10th" if year == "10th" else "2nd_PU"
            questions = db_manager.get_questions_by_subject(subject, board, course, class_level)
            
            if not questions:
                flash('No questions available for this subject. Please try another subject.', 'warning')
                return render_template('student/generate.html')
            
            # Generate paper using semantic analyzer
            selected_questions = semantic_analyzer.generate_paper_questions(questions, difficulty, 20)
            
            # Generate PDF
            paper_config = {
                'subject': subject,
                'difficulty': difficulty,
                'board': board,
                'year': year,
                'course': course
            }
            
            output_path = pdf_manager.generate_question_paper(selected_questions, paper_config)
            
            # Record download
            db_manager.add_download(
                user_id=current_user.id,
                download_type='GENERATED_PAPER',
                subject=subject,
                difficulty=difficulty,
                file_path=output_path,
                is_free=True
            )
            
            # Increment free downloads
            db_manager.increment_free_downloads(current_user.id)
            
            flash(f'Practice paper generated successfully! Difficulty: {difficulty.title()}', 'success')
            return send_file(output_path, as_attachment=True)
        
        except Exception as e:
            flash(f'Error generating paper: {str(e)}', 'danger')
    
    return render_template('student/generate.html')

@app.route('/student/download/<int:paper_id>')
@login_required
def download_paper(paper_id):
    """Download a specific paper"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Check download eligibility
    free_downloads_used = db_manager.get_user_free_downloads_used(current_user.id)
    if free_downloads_used >= 2:
        # Store paper_id in session for after payment
        session['pending_paper_id'] = paper_id
        return redirect(url_for('payment_required'))
    
    # Get paper
    papers = db_manager.execute_query("SELECT * FROM question_papers WHERE id = ?", (paper_id,))
    if not papers:
        flash('Paper not found.', 'danger')
        return redirect(url_for('student_papers'))
    
    paper = dict(papers[0])
    
    # Record download
    db_manager.add_download(
        user_id=current_user.id,
        download_type='PREVIOUS_YEAR',
        subject=paper['subject'],
        file_path=paper['file_path'],
        is_free=True
    )
    
    # Increment free downloads
    db_manager.increment_free_downloads(current_user.id)
    
    if os.path.exists(paper['file_path']):
        return send_file(paper['file_path'], as_attachment=True)
    else:
        flash('File not found on server.', 'danger')
        return redirect(url_for('student_papers'))

@app.route('/student/payment')
@login_required
def payment_required():
    """Payment page for premium downloads"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    return render_template('student/payment.html')

@app.route('/student/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process mock payment"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    import random
    
    # Generate transaction ID
    transaction_id = f"TXN{datetime.now().strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
    
    # Add payment record
    db_manager.add_payment(
        transaction_id=transaction_id,
        user_id=current_user.id,
        amount=40.00,
        description="PDF Download Payment"
    )
    
    # Check if we have pending paper info (new flow)
    pending_paper_info = session.get('pending_paper_info')
    
    if pending_paper_info:
        # Generate the PDF they paid for
        year = pending_paper_info['year']
        board = pending_paper_info['board']
        course = pending_paper_info['course']
        subject = pending_paper_info['subject']
        paper_type = pending_paper_info.get('paper_type', 'PREVIOUS_YEAR')
        
        try:
            # Get questions
            class_level = "10th" if year == "10th" else "2nd_PU"
            all_questions = db_manager.get_questions_by_subject(subject, board, course, class_level)
            
            if paper_type == 'PREVIOUS_YEAR':
                # Generate frequency-sorted PDF
                grouped_questions = semantic_analyzer.group_similar_questions(all_questions)
                sorted_groups = sorted(grouped_questions, key=lambda x: x['frequency'], reverse=True)
                
                pdf_filename = pdf_manager.generate_frequency_sorted_pdf(
                    grouped_questions=sorted_groups,
                    subject=subject,
                    year=year,
                    board=board,
                    course=course
                )
                
                # Record download as paid
                db_manager.add_download(
                    user_id=current_user.id,
                    download_type='PREVIOUS_YEAR',
                    subject=subject,
                    file_path=pdf_filename,
                    is_free=False
                )
                db_manager.increment_download_count(current_user.id, 'PREVIOUS_YEAR')
                
            elif paper_type == 'GENERATED_PAPER':
                # Generate practice paper with difficulty
                difficulty = session.get('pending_difficulty', 'medium')
                
                grouped_questions = semantic_analyzer.group_similar_questions(all_questions)
                sorted_groups = sorted(grouped_questions, key=lambda x: x['frequency'], reverse=True)
                
                from src.nlp.semantic_analyzer import SemanticAnalyzer
                analyzer = SemanticAnalyzer()
                categorized = analyzer.categorize_by_difficulty(sorted_groups)
                
                if difficulty == 'easy':
                    selected_questions = categorized['easy'][:20]
                elif difficulty == 'medium':
                    selected_questions = (categorized['easy'][:10] + categorized['medium'][:10])
                else:
                    selected_questions = (categorized['medium'][:10] + categorized['hard'][:10])
                
                pdf_filename = pdf_manager.generate_practice_paper(
                    selected_questions,
                    subject,
                    difficulty,
                    year,
                    board,
                    course
                )
                
                # Record download as paid
                db_manager.add_download(
                    user_id=current_user.id,
                    download_type='GENERATED_PAPER',
                    subject=subject,
                    difficulty=difficulty,
                    file_path=pdf_filename,
                    is_free=False
                )
                db_manager.increment_download_count(current_user.id, 'GENERATED_PAPER')
            
            # Clear pending info from session
            session.pop('pending_paper_info', None)
            session.pop('pending_difficulty', None)
            
            # Store download file for success page
            session['download_file'] = pdf_filename
            session['download_title'] = f"{subject} - {'Previous Year' if paper_type == 'PREVIOUS_YEAR' else 'Practice'} Paper"
            session['transaction_id'] = transaction_id
            
            # Redirect to download success
            return redirect(url_for('download_success'))
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in process_payment: {error_details}")
            flash(f'Error generating paper after payment: {str(e)}', 'danger')
            return redirect(url_for('student_dashboard'))
    
    # Fallback for old flow
    pending_paper_id = session.get('pending_paper_id')
    if pending_paper_id:
        papers = db_manager.execute_query("SELECT * FROM question_papers WHERE id = ?", (pending_paper_id,))
        if papers:
            paper = dict(papers[0])
            db_manager.add_download(
                user_id=current_user.id,
                download_type='PREVIOUS_YEAR',
                subject=paper['subject'],
                file_path=paper['file_path'],
                is_free=False
            )
            session.pop('pending_paper_id', None)
            session['payment_success'] = {
                'transaction_id': transaction_id,
                'paper_title': paper['title'],
                'file_path': paper['file_path']
            }
            return redirect(url_for('download_after_payment'))
    
    flash(f'Payment successful! Transaction ID: {transaction_id}', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/download-success')
@login_required
def download_success():
    """Download page after successful generation"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get download info from session
    download_file = session.get('download_file')
    download_title = session.get('download_title')
    transaction_id = session.get('transaction_id')
    
    if not download_file:
        flash('No pending download found.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Build file path for verification
    downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    file_path = os.path.join(downloads_dir, download_file)
    
    # Show download page (file should exist since generation succeeded)
    result = render_template('student/download_success.html',
                             paper_title=download_title,
                             transaction_id=transaction_id,
                             download_file=download_file)
    
    # Clear download info from session after rendering
    session.pop('download_file', None)
    session.pop('download_title', None)
    session.pop('transaction_id', None)
    
    return result

@app.route('/student/download-after-payment')
@login_required
def download_after_payment():
    """Download page after successful payment - legacy route"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    payment_info = session.get('payment_success')
    if not payment_info:
        flash('No pending download found.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Clear payment info from session
    session.pop('payment_success', None)
    
    file_path = payment_info['file_path']
    paper_title = payment_info['paper_title']
    transaction_id = payment_info['transaction_id']
    
    if os.path.exists(file_path):
        return render_template('student/download_success.html',
                             paper_title=paper_title,
                             transaction_id=transaction_id,
                             download_url=url_for('serve_paid_file', file_path=file_path))
    else:
        flash(f'Payment successful! Transaction ID: {transaction_id}. But file not found.', 'warning')
        return redirect(url_for('student_dashboard'))

@app.route('/student/serve-file')
@login_required
def serve_paid_file():
    """Serve the paid file"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    file_path = request.args.get('file_path')
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/student/download-file/<filename>')
@login_required
def download_file(filename):
    """Download generated PDF file"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Use the configured download folder
    downloads_dir = app.config['DOWNLOAD_FOLDER']
    file_path = os.path.join(downloads_dir, filename)
    
    # Debug: print file path
    print(f"Looking for file: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        # Try alternate location
        alt_path = os.path.join(os.path.dirname(__file__), 'downloads', filename)
        print(f"Trying alternate path: {alt_path}")
        if os.path.exists(alt_path):
            return send_file(alt_path, as_attachment=True, download_name=filename)
        
        flash(f'File not found: {filename}', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Get statistics
    total_papers = len(db_manager.get_question_papers())
    
    # Calculate total payment amount
    payments = db_manager.get_payments()
    total_payment_amount = sum(payment['amount'] for payment in payments)
    total_payment_count = len(payments)
    
    total_downloads = len(db_manager.get_download_logs())
    
    return render_template('admin/dashboard.html',
                         total_papers=total_papers,
                         total_payments=total_payment_amount,
                         total_payment_count=total_payment_count,
                         total_downloads=total_downloads)

@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload():
    """Upload question paper"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        year = request.form.get('year')
        board = request.form.get('board')
        course = request.form.get('course')
        subject = request.form.get('subject')
        class_level = request.form.get('class_level')
        
        # Get file
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return render_template('admin/upload.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return render_template('admin/upload.html')
        
        if not file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are allowed.', 'danger')
            return render_template('admin/upload.html')
        
        try:
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Add to database
            paper_id = db_manager.add_question_paper(
                title=title,
                year=int(year),
                board=board,
                course=course if class_level == '2nd_PU' else None,
                subject=subject,
                class_level=class_level,
                file_path=filepath,
                uploaded_by=current_user.id
            )
            
            # Extract questions from PDF
            try:
                paper_info = {
                    'id': paper_id,
                    'subject': subject,
                    'board': board,
                    'course': course if class_level == '2nd_PU' else None,
                    'class_level': class_level,
                    'year': int(year)
                }
                
                questions = pdf_manager.process_uploaded_paper(filepath, paper_info, db_manager)
                
                if questions:
                    flash(f'✅ Paper uploaded! {len(questions)} questions extracted automatically.', 'success')
                else:
                    flash(f'✅ Paper uploaded (ID: {paper_id}). No questions extracted - you can extract them manually.', 'info')
            except Exception as extract_error:
                print(f"Question extraction error: {extract_error}")
                flash(f'✅ Paper uploaded (ID: {paper_id}), but question extraction failed. You can try manually.', 'warning')
            
            return redirect(url_for('admin_papers'))
        
        except Exception as e:
            flash(f'Upload failed: {str(e)}', 'danger')
    
    return render_template('admin/upload.html')

@app.route('/admin/papers')
@admin_required
def admin_papers():
    """View all papers"""
    papers = db_manager.get_question_papers()
    return render_template('admin/papers.html', papers=papers)

@app.route('/admin/extract-questions/<int:paper_id>', methods=['POST'])
@admin_required
def admin_extract_questions(paper_id):
    """Manually extract questions from a specific paper"""
    try:
        # Get paper info
        papers = db_manager.get_question_papers()
        paper = next((p for p in papers if p['id'] == paper_id), None)
        
        if not paper:
            flash('Paper not found.', 'danger')
            return redirect(url_for('admin_papers'))
        
        paper_info = {
            'id': paper['id'],
            'subject': paper['subject'],
            'board': paper['board'],
            'course': paper['course'],
            'class_level': paper['class_level'],
            'year': paper['year']
        }
        
        # Extract questions
        questions = pdf_manager.process_uploaded_paper(paper['file_path'], paper_info, db_manager)
        
        if questions:
            flash(f'✅ Successfully extracted {len(questions)} questions from paper "{paper["title"]}"', 'success')
        else:
            flash(f'⚠️ No questions were extracted from paper "{paper["title"]}". Check PDF format.', 'warning')
    
    except Exception as e:
        flash(f'❌ Extraction failed: {str(e)}', 'danger')
    
    return redirect(url_for('admin_papers'))

@app.route('/admin/payments')
@admin_required
def admin_payments():
    """View all payments"""
    payments = db_manager.get_payments()
    return render_template('admin/payments.html', payments=payments)

@app.route('/admin/downloads')
@admin_required
def admin_downloads():
    """View download logs"""
    downloads = db_manager.get_download_logs()
    return render_template('admin/downloads.html', downloads=downloads)

# Request teardown
@app.teardown_appcontext
def close_db_connection(error):
    """Close database connection after each request"""
    db_manager.close_connection()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

if __name__ == '__main__':
    # Initialize database
    db_manager.initialize_database()
    
    # Run app
    print("Database initialized successfully!")
    print("Starting PrediQ Web Application...")
    print("Access at: http://localhost:5000")
    print("Admin: admin@prediq.com / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)