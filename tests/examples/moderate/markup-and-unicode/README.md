# Text with markup characters and other scripts

Level: moderate. Titles, columns, cells, labels and captions holding < > & and quotes
show as typed, never as markup; Greek, CJK and accented text is written as UTF-8.

Input:    `python build.py`
Expected: expected/site/... with &lt; &amp; escapes and the Unicode text unchanged
