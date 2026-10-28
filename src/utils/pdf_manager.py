"""
PDF Manager for PrediQ Application
Handles PDF processing, question extraction, and paper generation
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import tempfile

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import black, blue, red
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.nlp.semantic_analyzer import SemanticAnalyzer

class PDFManager:
    """Manages PDF operations for question papers"""
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        
        # Get project directories (3 levels up: utils -> src -> PrediQ)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.uploads_dir = os.path.join(project_root, 'uploads')
        self.downloads_dir = os.path.join(project_root, 'downloads')
        
        # Debug logging
        print(f"PDFManager initialized with downloads_dir: {self.downloads_dir}")
        
        # Ensure directories exist
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not PYPDF2_AVAILABLE:
            # Fallback: return dummy text
            return "PDF text extraction requires PyPDF2 library. Sample question text for testing."
        
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text.strip()
        
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    def parse_questions_from_text(self, text: str, paper_info: Dict) -> List[Dict]:
        """Parse individual questions from extracted text"""
        if not text:
            return []
        
        questions = []
        
        # Basic question parsing - looks for numbered questions
        # This is a simplified implementation; real parsing would be more sophisticated
        
        # Split by common question number patterns
        import re
        
        # Try different patterns for question numbering
        patterns = [
            r'(?:^|\n)\s*(\d+)\.\s*',  # "1. Question text"
            r'(?:^|\n)\s*Q\.?\s*(\d+)\s*[.:]?\s*',  # "Q.1" or "Q 1:"
            r'(?:^|\n)\s*Question\s*(\d+)\s*[.:]?\s*',  # "Question 1:"
        ]
        
        best_split = None
        max_questions = 0
        
        for pattern in patterns:
            try:
                # Split by pattern
                parts = re.split(pattern, text, flags=re.MULTILINE | re.IGNORECASE)
                
                # Remove empty parts and organize into question pairs
                if len(parts) > 2:  # At least one question found
                    question_count = (len(parts) - 1) // 2
                    if question_count > max_questions:
                        max_questions = question_count
                        best_split = parts
            except:
                continue
        
        if best_split and max_questions > 0:
            # Process the best split
            for i in range(1, len(best_split), 2):
                if i + 1 < len(best_split):
                    question_num = best_split[i]
                    question_text = best_split[i + 1].strip()
                    
                    if question_text and len(question_text) > 10:  # Filter very short texts
                        # Clean up question text
                        question_text = re.sub(r'\s+', ' ', question_text)
                        question_text = question_text[:1000]  # Limit length
                        
                        question_data = {
                            'question_number': int(question_num) if question_num.isdigit() else len(questions) + 1,
                            'question_text': question_text,
                            'subject': paper_info.get('subject', ''),
                            'board': paper_info.get('board', ''),
                            'course': paper_info.get('course'),
                            'class_level': paper_info.get('class_level', ''),
                            'year': paper_info.get('year', datetime.now().year),
                            'paper_id': paper_info.get('id'),
                            'question_type': self._determine_question_type(question_text),
                            'marks': self._estimate_marks(question_text),
                            'last_appeared_year': paper_info.get('year', datetime.now().year)
                        }
                        
                        questions.append(question_data)
        
        # If no questions found with patterns, try to split by sentences as fallback
        if not questions and text:
            sentences = text.split('.')
            for i, sentence in enumerate(sentences[:10]):  # Limit to first 10 sentences
                sentence = sentence.strip()
                if len(sentence) > 20:  # Only meaningful sentences
                    question_data = {
                        'question_number': i + 1,
                        'question_text': sentence + '.',
                        'subject': paper_info.get('subject', ''),
                        'board': paper_info.get('board', ''),
                        'course': paper_info.get('course'),
                        'class_level': paper_info.get('class_level', ''),
                        'year': paper_info.get('year', datetime.now().year),
                        'paper_id': paper_info.get('id'),
                        'question_type': 'SHORT',
                        'marks': 2,
                        'last_appeared_year': paper_info.get('year', datetime.now().year)
                    }
                    questions.append(question_data)
        
        return questions
    
    def _determine_question_type(self, question_text: str) -> str:
        """Determine question type based on content"""
        text_lower = question_text.lower()
        
        # Check for multiple choice indicators
        if any(indicator in text_lower for indicator in ['a)', 'b)', 'c)', 'd)', 'choose', 'select']):
            return 'MCQ'
        
        # Check for long answer indicators
        if any(indicator in text_lower for indicator in ['explain', 'describe', 'discuss', 'analyze', 'elaborate']):
            return 'LONG'
        
        # Check for short answer indicators
        if any(indicator in text_lower for indicator in ['define', 'what is', 'name', 'list', 'state']):
            return 'SHORT'
        
        # Default based on length
        word_count = len(question_text.split())
        if word_count > 50:
            return 'LONG'
        elif word_count > 20:
            return 'MEDIUM'
        else:
            return 'SHORT'
    
    def _estimate_marks(self, question_text: str) -> int:
        """Estimate marks based on question content"""
        text_lower = question_text.lower()
        
        # Look for explicit mark mentions
        import re
        mark_pattern = r'(\d+)\s*mark'
        matches = re.findall(mark_pattern, text_lower)
        if matches:
            try:
                return int(matches[0])
            except:
                pass
        
        # Estimate based on question type and length
        word_count = len(question_text.split())
        
        if any(indicator in text_lower for indicator in ['explain', 'describe', 'discuss', 'analyze']):
            return 5 if word_count > 30 else 3
        elif any(indicator in text_lower for indicator in ['define', 'what is', 'name']):
            return 2
        elif 'a)' in text_lower and 'b)' in text_lower:  # MCQ
            return 1
        else:
            # Based on length
            if word_count > 50:
                return 5
            elif word_count > 25:
                return 3
            else:
                return 2
    
    def process_uploaded_paper(self, pdf_path: str, paper_info: Dict, db_manager) -> List[Dict]:
        """Process uploaded PDF and extract questions"""
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Parse questions from text
            questions = self.parse_questions_from_text(text, paper_info)
            
            # Add questions to database
            added_questions = []
            for question_data in questions:
                try:
                    question_id = db_manager.add_question(
                        question_text=question_data['question_text'],
                        paper_id=paper_info['id'],
                        subject=question_data['subject'],
                        board=question_data['board'],
                        course=question_data['course'],
                        class_level=question_data['class_level'],
                        question_type=question_data['question_type'],
                        marks=question_data['marks'],
                        difficulty_level='MEDIUM',  # Default, can be updated later
                        year=question_data['year']
                    )
                    question_data['id'] = question_id
                    added_questions.append(question_data)
                
                except Exception as e:
                    print(f"Failed to add question: {e}")
                    continue
            
            return added_questions
        
        except Exception as e:
            raise Exception(f"Failed to process PDF: {e}")
    
    def generate_question_paper(self, questions: List[Dict], paper_config: Dict) -> str:
        """Generate a new question paper PDF"""
        if not questions:
            raise ValueError("No questions provided for paper generation")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"paper_{paper_config.get('subject', 'general')}_{paper_config.get('difficulty', 'medium')}_{timestamp}.pdf"
        output_path = os.path.join(self.downloads_dir, filename)
        
        # Try ReportLab first, then FPDF as fallback
        if REPORTLAB_AVAILABLE:
            return self._generate_with_reportlab(questions, paper_config, output_path)
        elif FPDF_AVAILABLE:
            return self._generate_with_fpdf(questions, paper_config, output_path)
        else:
            # Create a simple text file as fallback
            return self._generate_text_paper(questions, paper_config, output_path.replace('.pdf', '.txt'))
    
    def _generate_with_reportlab(self, questions: List[Dict], paper_config: Dict, output_path: str) -> str:
        """Generate PDF using ReportLab"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=1*inch)
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=16,
                spaceAfter=30,
                textColor=blue
            )
            
            question_style = ParagraphStyle(
                'QuestionStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leftIndent=0
            )
            
            # Build content
            content = []
            
            # Title
            title = f"{paper_config.get('subject', 'Subject')} - {paper_config.get('difficulty', 'Medium').title()} Level"
            content.append(Paragraph(title, title_style))
            
            # Instructions
            instructions = """
            <b>Instructions:</b><br/>
            1. Read all questions carefully<br/>
            2. Answer all questions<br/>
            3. Time: 3 hours<br/>
            4. Maximum marks as indicated<br/>
            """
            content.append(Paragraph(instructions, styles['Normal']))
            content.append(Spacer(1, 20))
            
            # Questions
            for i, question in enumerate(questions, 1):
                # Question number and marks
                marks = question.get('marks', 2)
                year = question.get('last_appeared_year', '')
                year_text = f" [{year}]" if year else ""
                
                question_header = f"<b>Q{i}.</b> ({marks} marks){year_text}"
                content.append(Paragraph(question_header, styles['Normal']))
                
                # Question text
                question_text = question.get('question_text', '').strip()
                content.append(Paragraph(question_text, question_style))
                content.append(Spacer(1, 15))
            
            # Build PDF
            doc.build(content)
            
            return output_path
        
        except Exception as e:
            raise Exception(f"Failed to generate PDF with ReportLab: {e}")
    
    def _generate_with_fpdf(self, questions: List[Dict], paper_config: Dict, output_path: str) -> str:
        """Generate PDF using FPDF as fallback"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Title
            title = f"{paper_config.get('subject', 'Subject')} - {paper_config.get('difficulty', 'Medium').title()} Level"
            pdf.cell(0, 10, title, ln=True, align='C')
            pdf.ln(10)
            
            # Instructions
            pdf.set_font('Arial', '', 10)
            instructions = [
                "Instructions:",
                "1. Read all questions carefully",
                "2. Answer all questions",
                "3. Time: 3 hours",
                "4. Maximum marks as indicated"
            ]
            
            for instruction in instructions:
                pdf.cell(0, 6, instruction, ln=True)
            pdf.ln(10)
            
            # Questions
            pdf.set_font('Arial', '', 11)
            for i, question in enumerate(questions, 1):
                # Question number and marks
                marks = question.get('marks', 2)
                year = question.get('last_appeared_year', '')
                year_text = f" [{year}]" if year else ""
                
                question_header = f"Q{i}. ({marks} marks){year_text}"
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, question_header, ln=True)
                
                # Question text
                pdf.set_font('Arial', '', 10)
                question_text = question.get('question_text', '').strip()
                
                # Handle long text by splitting into lines
                lines = self._split_text_to_lines(question_text, 80)
                for line in lines:
                    pdf.cell(0, 6, line, ln=True)
                
                pdf.ln(5)
            
            pdf.output(output_path)
            return output_path
        
        except Exception as e:
            raise Exception(f"Failed to generate PDF with FPDF: {e}")
    
    def _generate_text_paper(self, questions: List[Dict], paper_config: Dict, output_path: str) -> str:
        """Generate text file as ultimate fallback"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Title
                title = f"{paper_config.get('subject', 'Subject')} - {paper_config.get('difficulty', 'Medium').title()} Level"
                f.write(f"{title}\n")
                f.write("=" * len(title) + "\n\n")
                
                # Instructions
                f.write("Instructions:\n")
                f.write("1. Read all questions carefully\n")
                f.write("2. Answer all questions\n")
                f.write("3. Time: 3 hours\n")
                f.write("4. Maximum marks as indicated\n\n")
                
                # Questions
                for i, question in enumerate(questions, 1):
                    marks = question.get('marks', 2)
                    year = question.get('last_appeared_year', '')
                    year_text = f" [{year}]" if year else ""
                    
                    f.write(f"Q{i}. ({marks} marks){year_text}\n")
                    f.write(f"{question.get('question_text', '').strip()}\n\n")
            
            return output_path
        
        except Exception as e:
            raise Exception(f"Failed to generate text file: {e}")
    
    def _split_text_to_lines(self, text: str, max_chars: int) -> List[str]:
        """Split text into lines of maximum character length"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line += (" " + word) if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def get_previous_year_papers(self, questions: List[Dict], subject: str) -> str:
        """Generate previous year papers compilation"""
        if not questions:
            return None
        
        # Group questions by frequency using semantic analyzer
        question_groups = self.semantic_analyzer.find_similar_questions(questions, 0.6)
        frequency_data = self.semantic_analyzer.calculate_question_frequencies(question_groups)
        
        # Generate paper configuration
        paper_config = {
            'subject': subject,
            'difficulty': 'previous_year',
            'type': 'compilation'
        }
        
        # Create previous year paper with frequency-sorted questions
        return self.generate_question_paper(frequency_data[:25], paper_config)
    
    def generate_frequency_sorted_pdf(self, grouped_questions: List[Dict], subject: str, 
                                      year: str, board: str, course: str = None) -> str:
        """
        Generate PDF with questions sorted by frequency with year stamps on top-right
        This is the MAIN functionality for "Previous Year Papers"
        """
        if not grouped_questions:
            raise ValueError("No questions provided")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PrevYear_{subject}_{year}_{timestamp}.pdf"
        filepath = os.path.join(self.downloads_dir, filename)
        
        try:
            # Try FPDF first (primary method)
            self._generate_frequency_pdf_fpdf(grouped_questions, subject, year, board, course, filepath)
            return filename
        except Exception as e:
            print(f"FPDF generation failed: {e}")
            try:
                # Fallback to ReportLab
                self._generate_frequency_pdf_reportlab(grouped_questions, subject, year, board, course, filepath)
                return filename
            except Exception as e2:
                raise Exception(f"Both PDF generation methods failed. FPDF: {e}, ReportLab: {e2}")
    
    def generate_practice_paper(self, selected_questions: List[Dict], subject: str,
                                difficulty: str, year: str, board: str, course: str = None) -> str:
        """
        Generate practice paper PDF based on difficulty level
        Questions are already selected based on frequency:
        - Easy: Mostly repeated questions (high frequency)
        - Medium: Mix of frequently and moderately repeated
        - Hard: Mix of moderate and rarely repeated questions
        """
        if not selected_questions:
            raise ValueError("No questions provided for practice paper")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Practice_{subject}_{difficulty}_{timestamp}.pdf"
        filepath = os.path.join(self.downloads_dir, filename)
        
        try:
            # Use FPDF for practice paper generation
            self._generate_practice_pdf_fpdf(selected_questions, subject, difficulty, year, board, course, filepath)
            print(f"Practice paper generated: {filename}")
            return filename
        except Exception as e:
            print(f"FPDF practice paper failed: {e}")
            try:
                # Fallback to ReportLab
                self._generate_practice_pdf_reportlab(selected_questions, subject, difficulty, year, board, course, filepath)
                return filename
            except Exception as e2:
                raise Exception(f"Both PDF generation methods failed. FPDF: {e}, ReportLab: {e2}")
    
    def _generate_practice_pdf_fpdf(self, questions: List[Dict], subject: str, difficulty: str,
                                   year: str, board: str, course: str, filepath: str) -> None:
        """Generate practice paper PDF using FPDF"""
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'{subject} - Practice Paper', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f'Difficulty: {difficulty.upper()} | {year} | {board}' + (f' | {course}' if course else ''), 0, 1, 'C')
        pdf.ln(10)
        
        # Instructions
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(0, 5, 'Instructions: Attempt all questions. Each question carries marks as indicated.', 0, 'L')
        pdf.ln(5)
        
        # Questions
        question_number = 1
        total_marks = 0
        
        for q_data in questions:
            if pdf.get_y() > 260:
                pdf.add_page()
            
            marks = q_data.get('marks', 1)
            total_marks += marks
            
            # Question text
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(0, 0, 0)
            question_text = f"{question_number}. {q_data.get('question_text', 'N/A')}"
            pdf.multi_cell(0, 6, question_text, 0, 'L')
            
            # Marks indication
            pdf.set_font('Arial', 'I', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"   [Marks: {marks}]", 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            question_number += 1
        
        # Footer with total marks
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, f'Total Marks: {total_marks}', 0, 1, 'R')
        
        pdf.output(filepath)
    
    def _generate_practice_pdf_reportlab(self, questions: List[Dict], subject: str, difficulty: str,
                                        year: str, board: str, course: str, filepath: str) -> None:
        """Generate practice paper PDF using ReportLab"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            alignment=1  # Center
        )
        story.append(Paragraph(f'{subject} - Practice Paper', title_style))
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=20,
            alignment=1
        )
        subtitle_text = f'Difficulty: {difficulty.upper()} | {year} | {board}'
        if course:
            subtitle_text += f' | {course}'
        story.append(Paragraph(subtitle_text, subtitle_style))
        
        # Instructions
        inst_style = ParagraphStyle('Instructions', parent=styles['Italic'], fontSize=9, spaceAfter=15)
        story.append(Paragraph('Instructions: Attempt all questions. Each question carries marks as indicated.', inst_style))
        
        # Questions
        question_style = ParagraphStyle(
            'Question',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        )
        marks_style = ParagraphStyle(
            'Marks',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#95a5a6'),
            spaceAfter=15
        )
        
        total_marks = 0
        for i, q_data in enumerate(questions, 1):
            marks = q_data.get('marks', 1)
            total_marks += marks
            
            # Question
            question_text = f"{i}. {q_data.get('question_text', 'N/A')}"
            story.append(Paragraph(question_text, question_style))
            
            # Marks
            story.append(Paragraph(f"[Marks: {marks}]", marks_style))
        
        # Total marks
        story.append(Spacer(1, 0.3*inch))
        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            alignment=2  # Right
        )
        story.append(Paragraph(f'Total Marks: {total_marks}', total_style))
        
        doc.build(story)
    
    def _generate_frequency_pdf_fpdf(self, grouped_questions: List[Dict], subject: str,
                                     year: str, board: str, course: str, filepath: str) -> None:
        """Generate frequency-sorted PDF using FPDF"""
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'{subject} - Previous Year Questions', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f'{year} | {board}' + (f' | {course}' if course else ''), 0, 1, 'C')
        pdf.cell(0, 8, 'Questions Sorted by Frequency (Most Asked First)', 0, 1, 'C')
        pdf.ln(10)
        
        # Questions
        question_number = 1
        for q_data in grouped_questions:
            if pdf.get_y() > 250:
                pdf.add_page()
            
            current_y = pdf.get_y()
            years_text = ', '.join(str(y) for y in q_data.get('years', []))
            
            # Year stamp box on top-right
            pdf.set_xy(155, current_y)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(230, 230, 230)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(45, 6, f"Year: {years_text}", 1, 0, 'C', True)
            
            # Question text on left
            pdf.set_xy(10, current_y)
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(140, 6, f"{question_number}. {q_data['question_text']}", 0, 'L')
            
            # Frequency info
            pdf.set_font('Arial', 'I', 9)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 5, f"   Frequency: Asked {q_data['frequency']} time(s) | Marks: {q_data.get('marks', 1)}", 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            question_number += 1
        
        pdf.output(filepath)
    
    def _generate_frequency_pdf_reportlab(self, grouped_questions: List[Dict], subject: str,
                                         year: str, board: str, course: str, filepath: str) -> None:
        """Generate frequency-sorted PDF using ReportLab"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                    fontSize=16, textColor=colors.HexColor('#1e3a8a'),
                                    spaceAfter=12, alignment=1)
        
        story.append(Paragraph(f'{subject} - Previous Year Questions', title_style))
        story.append(Paragraph(f'{year} | {board}' + (f' | {course}' if course else ''), styles['Normal']))
        story.append(Paragraph('Questions Sorted by Frequency (Most Asked First)', styles['Italic']))
        story.append(Spacer(1, 0.3*inch))
        
        # Questions
        question_style = ParagraphStyle('Question', parent=styles['BodyText'],
                                       fontSize=11, leading=14, spaceAfter=6)
        year_style = ParagraphStyle('Year', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.black,
                                   alignment=1, fontName='Helvetica-Bold')
        
        for idx, q_data in enumerate(grouped_questions, 1):
            years_text = ', '.join(str(y) for y in q_data.get('years', []))
            question_text = f"{idx}. {q_data['question_text']}"
            year_text = f"Year: {years_text}"
            
            table_data = [[Paragraph(question_text, question_style),
                          Paragraph(year_text, year_style)]]
            
            t = Table(table_data, colWidths=[4.5*inch, 2*inch])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('BOX', (1, 0), (1, 0), 1, colors.black),
                ('BACKGROUND', (1, 0), (1, 0), colors.Color(0.9, 0.9, 0.9)),
                ('TOPPADDING', (1, 0), (1, 0), 3),
                ('BOTTOMPADDING', (1, 0), (1, 0), 3),
            ]))
            
            story.append(t)
            freq_text = f"Frequency: Asked {q_data['frequency']} time(s) | Marks: {q_data.get('marks', 1)}"
            story.append(Paragraph(freq_text, styles['Italic']))
            story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)


# Utility function for testing
def test_pdf_manager():
    """Test PDF manager functionality"""
    print("Testing PDF Manager...")
    
    pdf_manager = PDFManager()
    
    # Test text parsing
    sample_text = """
    1. What is photosynthesis?
    Photosynthesis is the process by which plants make food.
    
    2. Define respiration in plants.
    Respiration is the process of breaking down food to release energy.
    
    3. Explain the importance of water in plants.
    Water is essential for various plant processes including photosynthesis.
    """
    
    paper_info = {
        'id': 1,
        'subject': 'Biology',
        'board': 'CBSE',
        'class_level': '10th',
        'year': 2023
    }
    
    questions = pdf_manager.parse_questions_from_text(sample_text, paper_info)
    print(f"Parsed {len(questions)} questions")
    
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q['question_text'][:50]}... (Type: {q['question_type']}, Marks: {q['marks']})")
    
    # Test paper generation
    if questions:
        try:
            paper_config = {
                'subject': 'Biology',
                'difficulty': 'medium',
                'class_level': '10th'
            }
            
            output_path = pdf_manager.generate_question_paper(questions, paper_config)
            print(f"Generated paper: {output_path}")
        
        except Exception as e:
            print(f"Paper generation failed: {e}")
    
    print("Test completed!")


if __name__ == "__main__":
    test_pdf_manager()
