# Datheon — تحليل المستندات باستخدام Gemini

أداة Python بسيطة لتحويل النصوص غير المنظمة للفواتير والسير الذاتية إلى JSON.
تستخدم Gemini Structured Outputs ثم تتحقق محليًا من النتيجة باستخدام Pydantic.
الحزمة المستخدمة هي `google-genai` الرسمية الحالية، بدلًا من `google-generativeai` القديمة.

## التثبيت والتشغيل على Windows

يتطلب Python 3.12 أو أحدث. بعد استنساخ المستودع، افتح PowerShell داخل مجلد `task1`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

افتح `.env` وضع مفتاحك فقط في `GEMINI_API_KEY`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

يمكنك إنشاء المفتاح من [Google AI Studio](https://aistudio.google.com/apikey).
اختر نموذجًا متاحًا لحسابك يدعم Structured Outputs؛ يمكن تغييره في `.env` أو عبر `--model`.
متغيرات البيئة الموجودة تتقدم على إعدادات `.env`. المفتاح غير موجود في الكود وملف `.env` مستثنى من Git.

تحليل فاتورة وطباعة JSON في الطرفية:

```powershell
.\.venv\Scripts\python.exe main.py invoice examples/invoice.txt
```

تحليل سيرة ذاتية:

```powershell
.\.venv\Scripts\python.exe main.py resume examples/cv.txt
```

تظهر النتيجة في الطرفية بعد التحقق منها. استخدم `--help` لعرض الخيارات.
يمكن استبدال مسار المثال بأي ملف نصي UTF-8 بالعربية أو الإنجليزية.
المدخلات نصوص فقط: ملفات PDF وWord والصور تحتاج استخراج النص أو OCR قبل تمريرها للأداة.

## تقسيم الملفات

```text
main.py                  نقطة التشغيل
analyzer/
  cli.py                 قراءة الملف والإعدادات وطباعة الناتج
  extractor.py           طلب Gemini والتحقق من الاستجابة
  schemas.py             مخططات Invoice وResume والحقول المتداخلة
  prompts.py             قالب prompt بمعاملات وأمثلة ثابتة مستقلة عن ملفات الإدخال
examples/
  invoice.txt / .json     مثال إنكليزي ونتيجة متوقعة
  cv.txt / resume.json    سيرة ذاتية إنكليزية ونتيجة توضيحية
tests/test_analyzer.py    اختبارات محلية دون استدعاء API
.env.example             إعدادات قابلة للنسخ
requirements.txt         الاعتماديات
```

## قواعد التحقق

- جميع مفاتيح المخطط مطلوبة؛ الحقائق غير الموجودة تكون `null`، والقوائم الغائبة `[]`.
- تُرفض الحقول الإضافية، حتى داخل العناصر المتداخلة، ولا تُحوّل النصوص الرقمية إلى أرقام تلقائيًا.
- تواريخ الفواتير `YYYY-MM-DD`، والعملات ثلاثة أحرف كبيرة، والأرقام يجب أن تكون محدودة.
- تُقبل القيم السالبة لفواتير الخصم. تُحفظ القيم المذكورة دون تعديل حسابي.
- `warnings` مخصص للغموض والتناقضات التي يلاحظها النموذج؛ لا توجد مطابقة حسابية محلية للمجاميع.
- استجابات JSON غير الصالحة أو المحجوبة أو المبتورة تُرفض، مع خروج برمز `1` دون طباعة JSON.
- الحد الأقصى للنص 100,000 محرف، ومهلة طلب الشبكة 60 ثانية.

التحقق يضمن بنية البيانات وأنواعها؛ صحة استخراج الحقائق تحتاج مراجعة عند الاستخدام.
مثال الإدخال: [examples/cv.txt](examples/cv.txt).
مثال الإخراج الذي شاركه المستخدم بعد التشغيل: [examples/resume.json](examples/resume.json).
قد تختلف صياغة النص الناتج بين تشغيل وآخر. مثال الفاتورة تعليمي.
يُرسل نص المستند إلى Google عند التشغيل؛ الاختبارات المحلية لا ترسل بيانات.

## الاختبارات

بعد تثبيت الاعتماديات:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

تغطي المخططين، والقيم المرفوضة، وغياب المفتاح، وفشل الاتصال، وطباعة JSON الصحيح فقط.
تستخدم بديلًا محليًا لاستجابة Gemini؛ اختبار الاتصال الحقيقي يحتاج مفتاحك وتشغيل أحد الأمرين أعلاه.

## المراجع

- [Google GenAI Python SDK](https://googleapis.github.io/python-genai/)
- [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Pydantic strict JSON validation](https://docs.pydantic.dev/latest/concepts/json/)
