# Flask Mini Chat Sayti

Bu loyiha **Flask** yordamida yozilgan oddiy chat ilovasidir. Foydalanuvchilar ro'yxatdan o'tib, tizimga kirib, umumiy chatda yoki bir-biri bilan xabar almashishlari mumkin.

## Ishga tushirish

1. Virtual muhitni yaratish:

```bash
python -m venv venv
```

2. Virtual muhitni faollashtirish:

- Windows (PowerShell):
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

- Windows (cmd):
  ```cmd
  .\venv\Scripts\activate
  ```

3. Talablarni o'rnatish:

```bash
pip install -r requirements.txt
```

4. Ilovani ishga tushirish:

```bash
python app.py
```

5. Brauzerda oching: http://127.0.0.1:5000

## Loyihaning tuzilishi

- `app.py` — Flask ilovasi va yo'nalishlar (routes)
- `templates/` — HTML shablonlar
- `static/` — CSS va JavaScript fayllar
- `chat.db` — SQLite ma'lumotlar bazasi (birinchi ishga tushganda yaratiladi)

## Kelajak talablari

- Real vaqt chat (WebSocket yordamida)
- Xabarlarni tahrirlash/o'chirish
- Profil sahifalari va onlayn foydalanuvchilar
