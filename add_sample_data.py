"""
Sample Data Populator for PrediQ
Adds comprehensive test data for all subjects and years
"""

import sqlite3
from datetime import datetime

def populate_sample_data():
    conn = sqlite3.connect('data/prediq.db')
    cursor = conn.cursor()
    
    print("Adding comprehensive sample data...")
    
    # Mathematics Questions for different years
    math_questions = [
        # 2024 Questions
        ("Solve the quadratic equation: x² + 5x + 6 = 0", "SHORT", 3, "MEDIUM", 2024, "CBSE", "10th"),
        ("Find the area of a triangle with sides 3cm, 4cm, and 5cm", "SHORT", 2, "EASY", 2024, "CBSE", "10th"),
        ("Prove that the sum of angles in a triangle is 180 degrees", "LONG", 4, "MEDIUM", 2024, "CBSE", "10th"),
        ("Differentiate y = x³ + 2x² - 5x + 7 with respect to x", "SHORT", 3, "MEDIUM", 2024, "CBSE", "10th"),
        ("Solve the system of linear equations: 2x + 3y = 12 and 3x - 2y = 5", "SHORT", 4, "HARD", 2024, "CBSE", "10th"),
        
        # 2023 Questions (some repeated from 2024)
        ("Solve the quadratic equation: x² + 5x + 6 = 0", "SHORT", 3, "MEDIUM", 2023, "CBSE", "10th"),
        ("Find the area of a triangle with sides 3cm, 4cm, and 5cm", "SHORT", 2, "EASY", 2023, "CBSE", "10th"),
        ("Find the equation of a line passing through (2,3) and perpendicular to y = 2x + 1", "SHORT", 5, "HARD", 2023, "CBSE", "10th"),
        ("Prove the Pythagorean theorem using coordinate geometry", "LONG", 6, "HARD", 2023, "CBSE", "10th"),
        ("Calculate the compound interest on Rs. 10000 at 8% per annum for 2 years", "SHORT", 3, "MEDIUM", 2023, "CBSE", "10th"),
        
        # 2022 Questions
        ("Solve the quadratic equation: x² + 5x + 6 = 0", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        ("Prove that the sum of angles in a triangle is 180 degrees", "LONG", 4, "MEDIUM", 2022, "CBSE", "10th"),
        ("Find the derivative of sin(x) + cos(x)", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        ("Solve the inequality: 3x - 7 > 2x + 5", "SHORT", 2, "EASY", 2022, "CBSE", "10th"),
        ("Find the volume of a cone with radius 5cm and height 12cm", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        
        # 2021 Questions
        ("Find the area of a triangle with sides 3cm, 4cm, and 5cm", "SHORT", 2, "EASY", 2021, "CBSE", "10th"),
        ("Prove the Pythagorean theorem using coordinate geometry", "LONG", 6, "HARD", 2021, "CBSE", "10th"),
        ("Solve the system of equations: x + y = 10 and x - y = 4", "SHORT", 3, "MEDIUM", 2021, "CBSE", "10th"),
        ("Find the median of the data set: 12, 15, 18, 20, 22, 25, 30", "SHORT", 2, "EASY", 2021, "CBSE", "10th"),
        ("Calculate simple interest on Rs. 5000 at 6% for 3 years", "SHORT", 2, "EASY", 2021, "CBSE", "10th"),
    ]
    
    # Physics Questions
    physics_questions = [
        # 2024
        ("State and prove Newton's second law of motion", "LONG", 5, "HARD", 2024, "CBSE", "10th"),
        ("Calculate the force required to accelerate a 10kg object at 5m/s²", "SHORT", 3, "MEDIUM", 2024, "CBSE", "10th"),
        ("Explain the principle of conservation of energy with examples", "LONG", 4, "MEDIUM", 2024, "CBSE", "10th"),
        ("Define velocity and acceleration. How are they related?", "SHORT", 3, "MEDIUM", 2024, "CBSE", "10th"),
        ("A ball is thrown upward with velocity 20m/s. Find maximum height", "SHORT", 4, "HARD", 2024, "CBSE", "10th"),
        
        # 2023
        ("State and prove Newton's second law of motion", "LONG", 5, "HARD", 2023, "CBSE", "10th"),
        ("Calculate the force required to accelerate a 10kg object at 5m/s²", "SHORT", 3, "MEDIUM", 2023, "CBSE", "10th"),
        ("Explain Ohm's law with circuit diagram", "LONG", 4, "MEDIUM", 2023, "CBSE", "10th"),
        ("Calculate resistance when V=12V and I=2A", "SHORT", 2, "EASY", 2023, "CBSE", "10th"),
        ("What is the difference between AC and DC current?", "SHORT", 3, "MEDIUM", 2023, "CBSE", "10th"),
        
        # 2022
        ("Calculate the force required to accelerate a 10kg object at 5m/s²", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        ("Explain the principle of conservation of energy with examples", "LONG", 4, "MEDIUM", 2022, "CBSE", "10th"),
        ("Define kinetic energy and derive its formula", "LONG", 5, "HARD", 2022, "CBSE", "10th"),
        ("Calculate work done when force 50N moves object 10m", "SHORT", 2, "EASY", 2022, "CBSE", "10th"),
        ("Explain the laws of reflection of light", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        
        # 2021
        ("State and prove Newton's second law of motion", "LONG", 5, "HARD", 2021, "CBSE", "10th"),
        ("Explain Ohm's law with circuit diagram", "LONG", 4, "MEDIUM", 2021, "CBSE", "10th"),
        ("What is potential energy? Give examples", "SHORT", 3, "MEDIUM", 2021, "CBSE", "10th"),
        ("Calculate power when work 1000J is done in 20s", "SHORT", 2, "EASY", 2021, "CBSE", "10th"),
        ("Explain electromagnetic induction", "LONG", 4, "MEDIUM", 2021, "CBSE", "10th"),
    ]
    
    # Chemistry Questions
    chemistry_questions = [
        # 2024
        ("Explain the periodic table trends for atomic radius", "LONG", 5, "HARD", 2024, "CBSE", "10th"),
        ("Balance the equation: H₂ + O₂ → H₂O", "SHORT", 2, "EASY", 2024, "CBSE", "10th"),
        ("What are the properties of acids and bases?", "SHORT", 4, "MEDIUM", 2024, "CBSE", "10th"),
        ("Define pH scale and its significance", "SHORT", 3, "MEDIUM", 2024, "CBSE", "10th"),
        ("Explain oxidation and reduction with examples", "LONG", 5, "HARD", 2024, "CBSE", "10th"),
        
        # 2023
        ("Explain the periodic table trends for atomic radius", "LONG", 5, "HARD", 2023, "CBSE", "10th"),
        ("Balance the equation: H₂ + O₂ → H₂O", "SHORT", 2, "EASY", 2023, "CBSE", "10th"),
        ("What is the difference between ionic and covalent bonds?", "SHORT", 4, "MEDIUM", 2023, "CBSE", "10th"),
        ("Calculate the molecular mass of H₂SO₄", "SHORT", 2, "EASY", 2023, "CBSE", "10th"),
        ("Explain the process of electrolysis of water", "LONG", 4, "MEDIUM", 2023, "CBSE", "10th"),
        
        # 2022
        ("Balance the equation: H₂ + O₂ → H₂O", "SHORT", 2, "EASY", 2022, "CBSE", "10th"),
        ("What are the properties of acids and bases?", "SHORT", 4, "MEDIUM", 2022, "CBSE", "10th"),
        ("Explain the structure of an atom", "LONG", 5, "HARD", 2022, "CBSE", "10th"),
        ("Define valency with examples", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        ("What is the law of conservation of mass?", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        
        # 2021
        ("Explain the periodic table trends for atomic radius", "LONG", 5, "HARD", 2021, "CBSE", "10th"),
        ("What are the properties of acids and bases?", "SHORT", 4, "MEDIUM", 2021, "CBSE", "10th"),
        ("Calculate moles in 44g of CO₂ (molecular mass 44)", "SHORT", 3, "MEDIUM", 2021, "CBSE", "10th"),
        ("Explain indicators and their use", "SHORT", 3, "MEDIUM", 2021, "CBSE", "10th"),
        ("What is a chemical reaction? Give types", "SHORT", 4, "MEDIUM", 2021, "CBSE", "10th"),
    ]
    
    # Biology Questions
    biology_questions = [
        # 2024
        ("Explain the process of photosynthesis with chemical equation", "LONG", 5, "HARD", 2024, "CBSE", "10th"),
        ("What is the function of mitochondria in cells?", "SHORT", 3, "MEDIUM", 2024, "CBSE", "10th"),
        ("Describe the structure and function of DNA", "LONG", 5, "HARD", 2024, "CBSE", "10th"),
        ("What are the differences between aerobic and anaerobic respiration?", "SHORT", 4, "MEDIUM", 2024, "CBSE", "10th"),
        ("Explain Mendel's law of inheritance", "LONG", 5, "HARD", 2024, "CBSE", "10th"),
        
        # 2023
        ("Explain the process of photosynthesis with chemical equation", "LONG", 5, "HARD", 2023, "CBSE", "10th"),
        ("What is the function of mitochondria in cells?", "SHORT", 3, "MEDIUM", 2023, "CBSE", "10th"),
        ("Describe the human digestive system", "LONG", 5, "HARD", 2023, "CBSE", "10th"),
        ("What is osmosis? Give examples", "SHORT", 3, "MEDIUM", 2023, "CBSE", "10th"),
        ("Explain the nitrogen cycle", "LONG", 4, "MEDIUM", 2023, "CBSE", "10th"),
        
        # 2022
        ("What is the function of mitochondria in cells?", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        ("What are the differences between aerobic and anaerobic respiration?", "SHORT", 4, "MEDIUM", 2022, "CBSE", "10th"),
        ("Explain the structure of human heart", "LONG", 5, "HARD", 2022, "CBSE", "10th"),
        ("What is the role of enzymes in digestion?", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        ("Define transpiration and its importance", "SHORT", 3, "MEDIUM", 2022, "CBSE", "10th"),
        
        # 2021
        ("Explain the process of photosynthesis with chemical equation", "LONG", 5, "HARD", 2021, "CBSE", "10th"),
        ("Describe the structure and function of DNA", "LONG", 5, "HARD", 2021, "CBSE", "10th"),
        ("What is the circulatory system? Explain", "LONG", 5, "HARD", 2021, "CBSE", "10th"),
        ("Define diffusion with examples", "SHORT", 2, "EASY", 2021, "CBSE", "10th"),
        ("Explain asexual reproduction in plants", "SHORT", 4, "MEDIUM", 2021, "CBSE", "10th"),
    ]
    
    # Insert questions
    subjects_data = [
        ("Mathematics", math_questions),
        ("Physics", physics_questions),
        ("Chemistry", chemistry_questions),
        ("Biology", biology_questions)
    ]
    
    for subject, questions in subjects_data:
        print(f"\nAdding {subject} questions...")
        for q in questions:
            question_text, q_type, marks, difficulty, year, board, class_level = q
            
            # Check if question already exists for this year
            cursor.execute("""
                SELECT id FROM questions 
                WHERE question_text = ? AND last_appeared_year = ? AND subject = ?
            """, (question_text, year, subject))
            
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO questions 
                    (question_text, question_type, marks, difficulty_level, 
                     frequency_count, last_appeared_year, paper_id, subject, 
                     board, class_level, created_date)
                    VALUES (?, ?, ?, ?, 1, ?, 1, ?, ?, ?, ?)
                """, (question_text, q_type, marks, difficulty, year, subject, 
                      board, class_level, datetime.now()))
                print(f"  ✓ Added: {question_text[:60]}... ({year})")
    
    # Update frequency counts for repeated questions
    print("\nCalculating frequency counts...")
    cursor.execute("""
        SELECT question_text, subject, COUNT(*) as freq, MAX(last_appeared_year) as latest_year
        FROM questions
        GROUP BY question_text, subject
        HAVING COUNT(*) > 1
    """)
    
    repeated_questions = cursor.fetchall()
    for row in repeated_questions:
        q_text, subject, freq, latest_year = row
        cursor.execute("""
            UPDATE questions 
            SET frequency_count = ?
            WHERE question_text = ? AND subject = ?
        """, (freq, q_text, subject))
        print(f"  ✓ Updated frequency: {q_text[:50]}... (asked {freq} times)")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ Sample data added successfully!")
    print("="*80)
    print("\nData Summary:")
    print(f"  • Mathematics: 20 questions (2021-2024)")
    print(f"  • Physics: 20 questions (2021-2024)")
    print(f"  • Chemistry: 20 questions (2021-2024)")
    print(f"  • Biology: 20 questions (2021-2024)")
    print(f"  • Total: 80 questions across 4 years")
    print(f"  • Some questions repeated across years to test frequency sorting")
    print("\nYou can now test:")
    print("  1. Previous Year Papers (will show year stamps)")
    print("  2. Practice Papers with different difficulty levels")
    print("  3. Frequency-based sorting (most asked questions first)")

if __name__ == "__main__":
    populate_sample_data()
