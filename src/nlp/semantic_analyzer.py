"""
Semantic Analyzer for PrediQ Application
Uses NLP techniques to identify similar questions and calculate frequency
"""

import re
import string
from typing import List, Dict, Tuple
from collections import Counter
import math

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class SemanticAnalyzer:
    """Analyzes questions for semantic similarity and frequency"""
    
    def __init__(self):
        self.stemmer = PorterStemmer() if NLTK_AVAILABLE else None
        self.stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
        self.vectorizer = TfidfVectorizer() if SKLEARN_AVAILABLE else None
        
        # Download required NLTK data if needed
        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                print("Downloading NLTK data...")
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text by cleaning, tokenizing, and stemming"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if NLTK_AVAILABLE:
            # Tokenize
            tokens = word_tokenize(text)
            
            # Remove stopwords and stem
            tokens = [
                self.stemmer.stem(token) 
                for token in tokens 
                if token not in self.stop_words and len(token) > 2
            ]
            
            return ' '.join(tokens)
        else:
            # Basic preprocessing without NLTK
            words = text.split()
            # Remove common stopwords manually
            basic_stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'}
            words = [word for word in words if word not in basic_stopwords and len(word) > 2]
            return ' '.join(words)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        processed_text1 = self.preprocess_text(text1)
        processed_text2 = self.preprocess_text(text2)
        
        if not processed_text1 or not processed_text2:
            return 0.0
        
        if SKLEARN_AVAILABLE:
            try:
                # Use TF-IDF and cosine similarity
                texts = [processed_text1, processed_text2]
                tfidf_matrix = self.vectorizer.fit_transform(texts)
                similarity_matrix = cosine_similarity(tfidf_matrix)
                return float(similarity_matrix[0][1])
            except Exception:
                pass
        
        # Fallback: Jaccard similarity
        return self._jaccard_similarity(processed_text1, processed_text2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity as fallback method"""
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_similar_questions(self, questions: List[Dict], similarity_threshold: float = 0.7) -> List[List[Dict]]:
        """Group similar questions together"""
        if not questions:
            return []
        
        # Create groups of similar questions
        groups = []
        processed_questions = []
        
        for question in questions:
            question_text = question.get('question_text', '')
            processed_text = self.preprocess_text(question_text)
            processed_questions.append({
                'original': question,
                'processed': processed_text,
                'grouped': False
            })
        
        # Group similar questions
        for i, question1 in enumerate(processed_questions):
            if question1['grouped']:
                continue
            
            # Start new group with this question
            current_group = [question1['original']]
            question1['grouped'] = True
            
            # Find similar questions
            for j, question2 in enumerate(processed_questions[i+1:], i+1):
                if question2['grouped']:
                    continue
                
                similarity = self.calculate_similarity(
                    question1['processed'], 
                    question2['processed']
                )
                
                if similarity >= similarity_threshold:
                    current_group.append(question2['original'])
                    question2['grouped'] = True
            
            groups.append(current_group)
        
        return groups
    
    def calculate_question_frequencies(self, question_groups: List[List[Dict]]) -> List[Dict]:
        """Calculate frequency and update questions with frequency data"""
        frequency_data = []
        
        for group in question_groups:
            # Count frequency as group size
            frequency = len(group)
            
            # Find the most recent year for this question type
            years = [q.get('last_appeared_year', 0) for q in group if q.get('last_appeared_year')]
            last_appeared_year = max(years) if years else 0
            
            # Use the first question as representative
            representative_question = group[0].copy()
            representative_question['frequency_count'] = frequency
            representative_question['last_appeared_year'] = last_appeared_year
            representative_question['similar_questions'] = group[1:] if len(group) > 1 else []
            
            frequency_data.append(representative_question)
        
        # Sort by frequency (descending) and then by year (descending)
        frequency_data.sort(
            key=lambda x: (x['frequency_count'], x['last_appeared_year']), 
            reverse=True
        )
        
        return frequency_data
    
    def categorize_by_difficulty(self, questions: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize questions by difficulty based on frequency"""
        if not questions:
            return {'easy': [], 'medium': [], 'hard': []}
        
        # Sort questions by frequency
        sorted_questions = sorted(
            questions, 
            key=lambda x: x.get('frequency_count', 1), 
            reverse=True
        )
        
        total_questions = len(sorted_questions)
        
        # Define thresholds (can be adjusted)
        easy_threshold = int(total_questions * 0.3)  # Top 30% most frequent
        medium_threshold = int(total_questions * 0.7)  # Next 40%
        
        easy_questions = sorted_questions[:easy_threshold]
        medium_questions = sorted_questions[easy_threshold:medium_threshold]
        hard_questions = sorted_questions[medium_threshold:]
        
        return {
            'easy': easy_questions,
            'medium': medium_questions,
            'hard': hard_questions
        }
    
    def generate_paper_questions(self, questions: List[Dict], difficulty: str, num_questions: int = 20) -> List[Dict]:
        """Generate questions for a paper based on difficulty"""
        categorized = self.categorize_by_difficulty(questions)
        
        if difficulty == 'easy':
            # 80% easy, 20% medium
            easy_count = int(num_questions * 0.8)
            medium_count = num_questions - easy_count
            selected = (
                categorized['easy'][:easy_count] + 
                categorized['medium'][:medium_count]
            )
        
        elif difficulty == 'medium':
            # 40% easy, 40% medium, 20% hard
            easy_count = int(num_questions * 0.4)
            medium_count = int(num_questions * 0.4)
            hard_count = num_questions - easy_count - medium_count
            selected = (
                categorized['easy'][:easy_count] + 
                categorized['medium'][:medium_count] +
                categorized['hard'][:hard_count]
            )
        
        else:  # hard
            # 20% easy, 30% medium, 50% hard
            easy_count = int(num_questions * 0.2)
            medium_count = int(num_questions * 0.3)
            hard_count = num_questions - easy_count - medium_count
            selected = (
                categorized['easy'][:easy_count] + 
                categorized['medium'][:medium_count] +
                categorized['hard'][:hard_count]
            )
        
        # Shuffle to randomize order while maintaining difficulty balance
        import random
        random.shuffle(selected)
        
        return selected[:num_questions]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text"""
        processed_text = self.preprocess_text(text)
        
        if not processed_text:
            return []
        
        words = processed_text.split()
        
        # Count word frequencies
        word_freq = Counter(words)
        
        # Get most common words as keywords
        keywords = [word for word, count in word_freq.most_common(max_keywords)]
        
        return keywords
    
    def analyze_paper_content(self, paper_text: str) -> Dict:
        """Analyze the content of a question paper"""
        # Extract questions from paper text (basic implementation)
        # This is a simplified version - in practice, you'd use more sophisticated parsing
        
        # Split by question numbers (assuming format like "1.", "2.", etc.)
        question_pattern = r'\d+\.\s*'
        questions = re.split(question_pattern, paper_text)
        questions = [q.strip() for q in questions if q.strip()]
        
        analysis = {
            'total_questions': len(questions),
            'questions': [],
            'keywords': self.extract_keywords(paper_text),
            'avg_question_length': 0
        }
        
        total_length = 0
        for i, question_text in enumerate(questions):
            question_data = {
                'id': i + 1,
                'text': question_text,
                'length': len(question_text.split()),
                'keywords': self.extract_keywords(question_text, 5)
            }
            analysis['questions'].append(question_data)
            total_length += question_data['length']
        
        if questions:
            analysis['avg_question_length'] = total_length / len(questions)
        
        return analysis
    
    def group_similar_questions(self, questions: List[Dict], similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Group similar questions and prepare data for PDF generation
        Returns list of question groups with frequency and year information
        """
        if not questions:
            return []
        
        # Group similar questions using existing method
        groups = self.find_similar_questions(questions, similarity_threshold)
        
        # Process groups to create frequency-sorted data
        grouped_data = []
        
        for group in groups:
            if not group:
                continue
            
            # Use first question as representative
            representative = group[0]
            
            # Collect all years this question appeared
            years = []
            for q in group:
                year = q.get('last_appeared_year')
                if year and year not in years:
                    years.append(year)
            
            # Debug: Print years found
            if len(group) > 1:
                print(f"DEBUG: Question '{representative.get('question_text', '')[:50]}...' appeared in years: {years}")
            
            # Sort years in descending order
            years.sort(reverse=True)
            
            # Create grouped question data
            question_data = {
                'question_text': representative.get('question_text', ''),
                'question_type': representative.get('question_type', 'SHORT'),
                'marks': representative.get('marks', 1),
                'frequency': len(group),  # Frequency = number of times it appeared
                'years': years,  # All years it appeared
                'last_year': years[0] if years else None,
                'subject': representative.get('subject', ''),
                'paper_id': representative.get('paper_id')
            }
            
            grouped_data.append(question_data)
        
        return grouped_data


# Utility functions for testing and demonstration
def test_semantic_analyzer():
    """Test the semantic analyzer with sample data"""
    analyzer = SemanticAnalyzer()
    
    # Sample questions
    sample_questions = [
        {
            'id': 1,
            'question_text': 'What is photosynthesis in plants?',
            'subject': 'Biology',
            'last_appeared_year': 2023
        },
        {
            'id': 2,
            'question_text': 'Explain the process of photosynthesis.',
            'subject': 'Biology',
            'last_appeared_year': 2022
        },
        {
            'id': 3,
            'question_text': 'Define photosynthesis and its importance.',
            'subject': 'Biology',
            'last_appeared_year': 2021
        },
        {
            'id': 4,
            'question_text': 'Calculate the area of a circle.',
            'subject': 'Mathematics',
            'last_appeared_year': 2023
        },
        {
            'id': 5,
            'question_text': 'Find the circumference of a circle.',
            'subject': 'Mathematics',
            'last_appeared_year': 2022
        }
    ]
    
    print("Testing Semantic Analyzer...")
    
    # Test similarity calculation
    print("\n1. Similarity Test:")
    sim1 = analyzer.calculate_similarity(
        sample_questions[0]['question_text'],
        sample_questions[1]['question_text']
    )
    print(f"Similarity between photosynthesis questions: {sim1:.3f}")
    
    sim2 = analyzer.calculate_similarity(
        sample_questions[0]['question_text'],
        sample_questions[3]['question_text']
    )
    print(f"Similarity between photosynthesis and circle area: {sim2:.3f}")
    
    # Test grouping
    print("\n2. Question Grouping:")
    groups = analyzer.find_similar_questions(sample_questions, 0.5)
    print(f"Found {len(groups)} question groups:")
    for i, group in enumerate(groups, 1):
        print(f"  Group {i}: {len(group)} questions")
        for q in group:
            print(f"    - {q['question_text'][:50]}...")
    
    # Test frequency calculation
    print("\n3. Frequency Analysis:")
    freq_data = analyzer.calculate_question_frequencies(groups)
    for q in freq_data:
        print(f"  Frequency {q['frequency_count']}: {q['question_text'][:50]}...")
    
    # Test difficulty categorization
    print("\n4. Difficulty Categorization:")
    categories = analyzer.categorize_by_difficulty(freq_data)
    for difficulty, questions in categories.items():
        print(f"  {difficulty.upper()}: {len(questions)} questions")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_semantic_analyzer()