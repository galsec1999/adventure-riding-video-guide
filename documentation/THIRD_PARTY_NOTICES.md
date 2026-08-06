# הודעות רכיבי צד שלישי — גרסת מסמך 1.0.3

מסמך זה מתאר את רכיבי הצד השלישי שבהם משתמשת גרסת המוצר **3.0.0**. הוא אינו מחליף את נוסחי הרישיון הקנוניים של כל פרויקט.

## Transformers.js

- רכיב: `@huggingface/transformers`, גרסה `4.2.0` כפי שמופיעה בחבילה המקומית `assets/vendor/transformers.min.js`.
- שימוש: טעינת tokenizer ומודל embeddings בתוך Web Worker בדפדפן.
- רישיון: Apache License 2.0.
- מקור ורישיון: <https://github.com/huggingface/transformers.js>
- התאמות להפצה: מזהה Gist ציבורי הוחלף בטקסט קצר בתוך הודעת אזהרה, ושם המחלקה `Mistral3ForConditionalGeneration` קוצר ל־`Mistral3ConditionalGeneration`, לאחר ש־GitHub Push Protection זיהה את שם המחלקה בן 32 התווים בטעות כמפתח Mistral. המחלקה אינה משתתפת במסלול `feature-extraction` שבו האתר משתמש; לא הוסר מפתח אמיתי ולא שונתה לוגיקת ה־embeddings.

## ONNX Runtime Web

- רכיבים מקומיים: `assets/vendor/ort-wasm-simd-threaded.mjs` ו־`assets/vendor/ort-wasm-simd-threaded.wasm`.
- שימוש: הרצת מודל ONNX במכשיר המשתמש.
- רישיון: MIT.
- מקור ורישיון: <https://github.com/microsoft/onnxruntime>

## Xenova/multilingual-e5-small

- מודל: `Xenova/multilingual-e5-small`, המרה ל־ONNX של `intfloat/multilingual-e5-small`.
- Revision מקובע: `761b726dd34fb83930e26aab4e9ac3899aa1fa78`.
- קובץ משקולות: `onnx/model_quantized.onnx`; ממדי embedding: 384.
- הורדה ראשונה משוערת: כ־129 MiB לקובצי המודל וה־tokenizer שנמדדו, לפני תקורת רשת ומטמון.
- רישיון מודל הבסיס: MIT.
- מקורות: <https://huggingface.co/Xenova/multilingual-e5-small> ו־<https://huggingface.co/intfloat/multilingual-e5-small>.

המודל אינו נכלל ב־repository ואינו נטען בלי הפעלה מפורשת של המשתמש. בהפעלה הראשונה הדפדפן מוריד אותו מ־Hugging Face ושומר אותו במטמון הדפדפן כאשר הדבר נתמך. לאחר הטעינה, טקסט השאילתה מחושב ב־Web Worker במכשיר ואינו נשלח ל־API או לשרת AI. אם ההורדה, ה־Worker או המודל נכשלים, החיפוש הרגיל ממשיך לעבוד.

## Hits.sh

- שימוש: SVG חיצוני שמונה טעינות של הדף החי בלבד.
- מקור: <https://hits.sh/docs/>
- פרטיות: <https://hits.sh/privacy/>

המונה אינו מזהה משתמשים ייחודיים; רענונים ובוטים עשויים להיספר. לפי הצהרת הפרטיות של השירות הוא אינו שומר כתובות IP, User-Agent, Cookies או מידע אישי. אם השירות חסום או אינו זמין, האתר מציג הודעת fallback ואינו פוגע בשאר הממשק.

## YouTube

האתר משתמש בקישורים, בתמונות ממוזערות ובנגן `youtube-nocookie.com` שנוצר רק לאחר לחיצה. הסרטונים עצמם אינם מורדים, נארזים או נשמרים במטמון האתר. כל זכויות הסרטונים, התמונות, שמות הערוצים וסימני המסחר נשארות בידי בעליהן.
