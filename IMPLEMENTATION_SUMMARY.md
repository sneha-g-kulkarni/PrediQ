# PrediQ - Main Functionality Implementation

## ✅ COMPLETED: Core Requirement

### Main Functionality Implemented:
When student completes all dropdown selections (year/board/course/subject) and clicks "View Previous Year Papers":

1. **Single PDF Generated** containing:
   - ALL questions from all uploaded papers for that selection
   - Questions sorted by frequency (descending - most asked first)
   - Year stamp displayed on top-right of each question
   - Frequency count shown (how many times it was asked)

2. **Semantic Analysis**:
   - Similar questions (same meaning, different wording) are grouped as ONE question
   - Uses TF-IDF vectorization and cosine similarity
   - Similarity threshold: 0.7 (can be adjusted)

3. **PDF Format**:
   - Professional layout with subject, year, board info
   - Each question numbered
   - Year stamp on right side showing all years it appeared
   - Frequency information below each question

## Implementation Details:

### New Files Created:
1. `templates/student/select.html` - Unified selection page

### Modified Files:
1. **app.py**:
   - Added `/student/select` route - unified selection page
   - Added `/student/view-previous-year` route - generates frequency-sorted PDF
   - Updated `/student/dashboard` to use separate download counters

2. **src/database/db_manager.py**:
   - Updated `user_sessions` table schema (prev_year_downloads, practice_downloads)
   - Added `get_user_download_stats()` method
   - Added `increment_download_count(type)` method

3. **src/nlp/semantic_analyzer.py**:
   - Added `group_similar_questions()` method
   - Groups similar questions by semantic similarity
   - Returns frequency-sorted data with year information

4. **src/utils/pdf_manager.py**:
   - Added `generate_frequency_sorted_pdf()` method
   - Generates PDF with questions sorted by frequency
   - Places year stamps on top-right corner
   - Supports both FPDF and ReportLab

5. **templates/student/dashboard.html**:
   - Updated to show separate download counters
   - Changed to link to unified selection page

## How It Works:

### Student Flow:
1. Student logs in → Dashboard
2. Clicks "Get Started"
3. Selects:
   - Year (10th or 2nd PU)
   - Board (for 10th: CBSE or State)
   - Course (for 2nd PU: PCMB or PCMC - auto Karnataka State Board)
   - Subject
4. Chooses action: **"View Previous Year Papers"** or "Generate Practice Paper"
5. For "View Previous Year Papers":
   - System fetches ALL questions from database for that selection
   - Semantic analyzer groups similar questions
   - Questions sorted by frequency (most asked → least asked)
   - PDF generated with year stamps on top-right
   - Student downloads PDF
6. Download counter incremented (separate for each type)
7. After 2 free downloads per type → ₹40 per additional download

### Admin Requirement:
- Admin must upload question papers first
- Questions are extracted and stored in database
- System then groups and sorts them for students

## Database Schema:

### user_sessions table:
```sql
- user_id
- prev_year_downloads (0-2 free, then paid)
- practice_downloads (0-2 free, then paid)
- last_reset_date
```

### downloads table:
```sql
- user_id
- download_type ('PREVIOUS_YEAR' or 'GENERATED_PAPER')
- subject
- file_path
- download_date
- is_free_download
- payment_id
```

## Next Steps to Test:

1. Run the application
2. Admin should upload some question papers with questions
3. Student can then:
   - Make selections
   - Click "View Previous Year Papers"
   - Get generated PDF with frequency-sorted questions

## Known Limitations:

1. **Question Extraction**: Currently admin needs to upload papers that are already in database
2. **PDF Parsing**: If questions need to be extracted from uploaded PDFs, additional work needed
3. **Difficulty Selection**: Not yet implemented for "Previous Year Papers" (client requirement clarification needed)

## Client Requirement Match:

✅ Single PDF with ALL questions
✅ Sorted by frequency (descending)  
✅ Semantic analyzer groups similar questions
✅ Year stamps on top-right
✅ Separate download limits (2 + 2 = 4 total free)
✅ ₹40 per additional download after free limit
⚠️ Difficulty level for previous year papers (needs clarification)
