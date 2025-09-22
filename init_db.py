# init_db.py — create PostgreSQL tables and seed internships
# init_db.py — create DB tables and seed internships
# init_db.py — create sqlite DB and seed internships
# init_db.py
import sqlite3
import os

DB = "internships.db"

if os.path.exists(DB):
    print("Removing old internships.db")
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()

# users table
c.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
""")

# profiles table
# Drop old DB before running this file
c.execute("""
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT,
    age INTEGER,
    gender TEXT,
    course TEXT,
    gpa REAL,
    skills TEXT,
    locations TEXT,
    roles TEXT,
    user_location TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")



# internships table
c.execute("""
CREATE TABLE internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    company TEXT,
    location TEXT,
    description TEXT,
    tags TEXT,
    stipend TEXT,
    url TEXT
);
""")

# seed internships (30-ish entries)
samples = [
    ("Backend Developer Intern","Acme Corp","Bengaluru","Work on Python APIs and microservices","python flask api sql backend","15000","https://example.com/a"),
    ("Java Developer Intern","TechVerse","Hyderabad","Assist in building enterprise Java applications","java spring hibernate backend","12000","https://example.com/b"),
    ("Node.js Intern","CodeWorks","Remote","Develop backend services in Node.js and Express","nodejs express mongodb backend","14000","https://example.com/c"),
    ("Frontend Intern","Pixel Labs","Pune","React + Tailwind UI work","javascript react css tailwind frontend","12000","https://example.com/d"),
    ("Web Designer Intern","DesignHub","Delhi","HTML, CSS, and Figma prototyping","html css figma uiux design","8000","https://example.com/e"),
    ("Fullstack Developer Intern","NextWeb","Remote","End-to-end MERN stack development","mongodb express react node fullstack","18000","https://example.com/f"),
    ("Data Science Intern","DataWorks","Hyderabad","NLP and model prototyping","python pandas sklearn nlp","20000","https://example.com/g"),
    ("Machine Learning Intern","AI Labs","Bengaluru","Work on supervised learning models","python tensorflow pytorch ml ai","22000","https://example.com/h"),
    ("Business Analyst Intern","Insight Corp","Mumbai","Data analysis & visualization for clients","excel sql tableau powerbi analytics","10000","https://example.com/i"),
    ("Computer Vision Intern","VisionTech","Chennai","Image recognition and deep learning models","opencv pytorch cnn vision","20000","https://example.com/j"),
    ("Cloud DevOps Intern","CloudWorks","Remote","CI/CD and infra automations","aws docker terraform cicd devops","22000","https://example.com/k"),
    ("Azure Intern","SoftTech","Noida","Work on Microsoft Azure cloud services","azure cloud networking devops","18000","https://example.com/l"),
    ("Kubernetes Intern","InfraTech","Gurgaon","Manage Kubernetes clusters","kubernetes docker helm devops cloud","21000","https://example.com/m"),
    ("Embedded Systems Intern","IoT Solutions","Chennai","C/C++ on microcontrollers","c cpp embedded iot microcontroller","18000","https://example.com/n"),
    ("Robotics Intern","RoboCorp","Pune","Assist in building robotic arms","robotics arduino ros python","16000","https://example.com/o"),
    ("IoT Firmware Intern","SmartHome Inc.","Bengaluru","Firmware for IoT devices","iot firmware embedded c esp32","17000","https://example.com/p"),
    ("Cybersecurity Intern","SecureNet","Delhi","Help perform penetration testing","cybersecurity linux networking ethical-hacking","19000","https://example.com/q"),
    ("SOC Analyst Intern","DefendTech","Hyderabad","Work in a Security Operations Center","security monitoring siem soc","15000","https://example.com/r"),
    ("Product Management Intern","NextGen","Mumbai","Assist PMs on market research","product management communication research","10000","https://example.com/s"),
    ("Digital Marketing Intern","AdWorks","Remote","SEO, Google Ads, and content marketing","seo google-ads marketing content","8000","https://example.com/t"),
    ("Operations Intern","BizOps","Delhi","Support business operations","operations management ms-excel","7000","https://example.com/u"),
    ("Graphic Design Intern","Creative Labs","Pune","Adobe Photoshop & Illustrator work","photoshop illustrator graphics design","6000","https://example.com/v"),
    ("UI/UX Intern","DesignStudio","Remote","Wireframing and prototyping in Figma","uiux figma sketch design","10000","https://example.com/w"),
    ("Content Writer Intern","WordWorks","Remote","Write blogs and social media content","writing editing content marketing","5000","https://example.com/x"),
    ("HR Intern","PeopleFirst","Bengaluru","Assist HR with recruitment","hr recruitment communication","6000","https://example.com/y"),
    ("Finance Intern","MoneyMatters","Mumbai","Financial modeling and Excel reporting","finance accounting excel","12000","https://example.com/z"),
    ("Legal Intern","LawTech","Delhi","Research corporate law cases","law contracts compliance legal","8000","https://example.com/aa"),
    ("Sales Intern","GrowthCorp","Gurgaon","Client outreach and sales support","sales communication crm","7000","https://example.com/ab"),
    ("Game Development Intern","GameVerse","Remote","Unity/C# game development","unity csharp game-development","15000","https://example.com/ac"),
]

c.executemany("INSERT INTO internships (title, company, location, description, tags, stipend, url) VALUES (?, ?, ?, ?, ?, ?, ?)", samples)

conn.commit()
conn.close()
print("✅ internships.db created and seeded")
