# פרויקט סיום סמינר: שחזור CyberLLMInstruct

## סקירת הפרויקט
פרויקט זה מכיל את קוד המקור המשמש לשחזור חלקי של המאמר: 
**"CyberLLMInstruct: A Pseudo-malicious Dataset Revealing Safety-performance Trade-offs in Cyber Security LLM Fine-tuning."** (ElZemity et al., 2025).

בעוד כותבי המאמר המקורי אימנו מודלים על גבי חומרה ארגונית (NVIDIA A100), הפרויקט שלנו התמקד באתגר של שחזור תהליך ה-Fine-tuning עבור המודל **Llama 3.1 8B** תחת מגבלות חומרה מקומיות קיצוניות (סביבת Intel Iris Xe). 
לשם כך, יצרנו ארכיטקטורת "אימון לסירוגין" (Intermittent Chunking) ונעזרנו בספריית הקוונטיזציה Unsloth.

## תוכן הארכיון (קבצי הקוד)
הארכיון מכיל את הסקריפטים הבאים שפותחו לטובת השחזור:

* **`split_dataset.py`**: אחראי על קריאת מאגר הנתונים ה"זדוני-לכאורה" (JSONL), ניקויו, ופיצולו באופן רנדומלי לסט אימון (90%) ולסט בדיקה (10%).
* **`train_unsloth_intermittent.py`**: צינור האימון (Fine-tuning) המרכזי. הסקריפט משלב את ספריית `Unsloth` (לאימון ב-4-bit) ומיישם לוגיקה ייחודית של "אימון במקטעים" (הגבלת זמן של 1.5 שעות, מקסימום 3 נקודות שמירה, וניקוי VRAM אגרסיבי) כדי למנוע קריסות OOM על החומרה המקומית.
* **`safety_evaluator.py`**: סקריפט הערכת בטיחות (Red-Teaming) הפועל במתודולוגיית LLM-as-a-Judge (באמצעות Gemini API) לסיווג פלטי המודל על פי הנחיות OWASP Top 10, במטרה להוכיח את קריסת מנגנוני הבטיחות כפי שמוצג במאמר.
* **`requirements.txt`**: רשימת הספריות והתלויות הדרושות להרצת הפרויקט בסביבת Python.

## הכרה במקורות (Source Acknowledgment)
הנתונים הגולמיים ושלד ההערכה הבסיסי הובאו מהמאגרים הרשמיים של כותבי המאמר:
* מקור הנתונים (54k דוגמאות): [Adelsamir01/CyberLLMInstruct](https://github.com/Adelsamir01/CyberLLMInstruct)
* בסיס מבחן CyberMetric: [cybermetric/CyberMetric](https://github.com/cybermetric/CyberMetric)

קוד המקור המצורף כאן מתמקד באופן בלעדי בהתאמת צינור ה-Fine-tuning לחומרה המוגבלת שלנו ובמנגנון השיפוט העצמאי.

## הוראות הרצה (סביבת Python)

יש לוודא התקנת Python (גרסה 3.9 ומעלה) ומומלץ להשתמש בסביבה וירטואלית (venv / conda).

### 1. התקנת התלויות
פתח את מסוף הפקודות (CMD, PowerShell או Terminal) והרץ:
```bash
pip install -r requirements.txt
```

### 2. הפעלת הסקריפטים בסדר כרונולוגי

**שלב א' - פיצול הנתונים:**
(יש לוודא שקובץ הנתונים הגולמי נמצא בנתיב `data/raw_cyberllminstruct.jsonl`)
```bash
python split_dataset.py
```

**שלב ב' - הרצת אימון מקורטע (Chunked Fine-Tuning):**
```bash
python train_unsloth_intermittent.py
```

**שלב ג' - הערכת בטיחות (Red Teaming):**
על מנת להריץ את הערכת הבטיחות, יש להגדיר את מפתח ה-API של Gemini כמשתנה סביבה (Environment Variable) לפני ההרצה:

**ב-Windows (Command Prompt / CMD):**
```cmd
set GEMINI_API_KEY=your_api_key_here
python safety_evaluator.py
```

**ב-Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
python safety_evaluator.py
```

**ב-Linux / macOS:**
```bash
export GEMINI_API_KEY="your_api_key_here"
python safety_evaluator.py
```
