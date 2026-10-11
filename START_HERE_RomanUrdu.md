# Hartus Floare CRM — Shuru karne ka tareeqa

Yeh aapke real-estate calls, leads, follow-ups, properties aur sales ke liye Django starter project hai.

## 1. Project chalana (Windows)

1. ZIP extract karein.
2. Project folder mein terminal / PowerShell kholein.
3. Python 3.12 ya naya installed hona chahiye.
4. Yeh commands one-by-one chalayein:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations crm
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

5. Browser mein `http://127.0.0.1:8000/` kholein aur superuser credentials se login karein.
6. Team users banane ke liye `http://127.0.0.1:8000/admin/` use kar sakte hain.

> Dependencies install karne ke liye pehli baar internet chahiye hoga.

## 2. Demo data

Dashboard ko sample records ke saath dekhne ke liye:

```powershell
python manage.py seed_demo --username YOUR_ADMIN_USERNAME --count 18
```

`YOUR_ADMIN_USERNAME` ki jagah woh username likhein jo `createsuperuser` ke waqt banaya tha. Demo records synthetic hain; asal client data nahi hai.

## 3. Claude Code ko kaise dena hai

1. `nexus_estate_crm` folder ko Claude Code mein open karein.
2. `CLAUDE.md` project instructions provide karta hai.
3. `.claude/skills/` mein Django architecture, premium UI, security, testing aur real-estate workflow ke focused skills maujood hain.
4. `CLAUDE_BUILD_PROMPT.md` khol kar uska prompt Claude Code ko dein. Isse Claude pehle code audit, tests aur verified improvements par kaam karega.
5. Har code change ke baad `python manage.py check` aur `python manage.py test` chalwayein.

## Abhi kya kaam karta hai?

Dashboard, lead records, manual call logging, property inventory, deal pipeline, commission calculation, task follow-ups, global search, CSV lead export aur Django admin ka starter implementation included hai.

**Zaroori farq:** App abhi khud phone call nahi lagata, aur WhatsApp/SMS/email integrations configured nahi hain. Calls ko manually CRM mein log kiya jata hai. Public production launch se pehle security settings, permissions, database backup, hosting aur tests ko review karna zaroori hai.
