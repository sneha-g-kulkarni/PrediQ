import sqlite3

conn = sqlite3.connect('prediq.db')
cursor = conn.cursor()

# Check questions
cursor.execute('SELECT id, question_text, year, frequency, marks, subject FROM questions LIMIT 10')
print("Current Questions:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Year: {row[2]}, Freq: {row[3]}, Marks: {row[4]}, Subject: {row[5]}")
    print(f"Question: {row[1][:80]}...")
    print("-" * 80)

conn.close()
