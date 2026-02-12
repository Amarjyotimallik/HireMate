# Resume Parsing Feature

## ✅ What's New

### 1. **Automatic Candidate Data Extraction**
The Upload Resume page now automatically extracts:
- **Candidate Name** (e.g., "Jyoti Prakash", "John Doe")
- **Email Address** (e.g., "jyotiprakash567890@gmail.com")
- **Position/Title** (e.g., "Backend Developer", "Frontend Engineer")

### 2. **HireMate Branding**
All assessment links now use: `https://hiremate.app/assessment/[token]`

---

## 🧪 How to Test

### Step 1: Upload a Resume
1. Navigate to **Upload Resume** page
2. Drag & drop `sample_resume.txt` or any text resume file
3. The system will automatically extract:
   - Name from the first lines of the resume
   - Email using regex pattern matching
   - Position using keyword detection

### Step 2: Watch the Extraction
The system uses intelligent parsing:

```javascript
// Name Extraction
- Looks for "Name:" field
- Checks first 3 lines for capitalized full names
- Validates 2-4 word names without numbers

// Email Extraction
- Regex: /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/

// Position Extraction
- Keywords: Developer, Engineer, Designer, Manager, etc.
- Matches: "Backend Developer", "Senior Frontend Engineer"
```

---

## 📄 Supported Resume Formats

Currently supports:
- **.txt** files (plain text)
- **.pdf** files (basic text extraction)
- **.doc/.docx** files (document formats)

### Sample Resume Format

```
YOUR NAME
Your Position

Email: your.email@example.com
Phone: +1234567890

EXPERIENCE
Senior Backend Developer
Company Name | 2020 - Present
```

---

## 🔧 For Production Enhancement

To improve PDF parsing, install a PDF parsing library:

```bash
npm install pdf-parse
```

Then import and use:
```javascript
import pdf from 'pdf-parse';

const extractTextFromPDF = async (file) => {
  const arrayBuffer = await file.arrayBuffer();
  const data = await pdf(arrayBuffer);
  return data.text;
};
```

---

## 🎯 Test File Included

Use `sample_resume.txt` in the root directory to test:
- ✅ Name: "JYOTI PRAKASH"
- ✅ Position: "Backend Developer"
- ✅ Email: "jyotiprakash567890@gmail.com"

---

## 🌐 Assessment Link Format

Old: ~~`https://skillsignal.ai/assessment/abc123`~~  
**New: `https://hiremate.app/assessment/abc123`**

---

## ⚡ Features

1. **Drag & Drop** - Easy file upload
2. **Real-time Parsing** - Instant data extraction
3. **Smart Fallbacks** - Defaults if data not found
4. **Email Validation** - Ensures valid email format
5. **Position Detection** - AI-powered job title extraction

---

## 🔄 Future Enhancements

- [ ] LinkedIn profile import
- [ ] Multi-page PDF support
- [ ] OCR for scanned resumes
- [ ] Multiple language support
- [ ] Skills extraction from resume
- [ ] Experience calculation
