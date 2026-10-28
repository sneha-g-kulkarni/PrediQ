import sqlite3

conn = sqlite3.connect('data/prediq.db')
cursor = conn.cursor()

# Check Mathematics questions with years
cursor.execute('''
    SELECT id, question_text, last_appeared_year, frequency_count, marks, subject 
    FROM questions 
    WHERE subject = "Mathematics"
    ORDER BY frequency_count DESC, last_appeared_year DESC
    LIMIT 10
''')

print("Mathematics Questions:")
print("="*100)
for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"Year: {row[2]}, Frequency: {row[3]}, Marks: {row[4]}")
    print(f"Question: {row[1][:80]}...")
    print("-"*100)

conn.close()
