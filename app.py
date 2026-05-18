import os
import csv
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = 'solapur_university_osm_secure_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'answer_sheets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_FILE = os.path.join(BASE_DIR, 'marks_db.json')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({"locked": [], "data": {}}, f)

def load_permanent_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"locked": [], "data": {}}

def save_permanent_db(db_data):
    with open(DB_FILE, 'w') as f:
        json.dump(db_data, f, indent=4)

# 📊 Q.1 ते Q.7 उपप्रश्नांची संपूर्ण मॅट्रिक्स रचना
GLOBAL_STRUCTURE = []

# Q.1 (Objective - १ ते १४ उपप्रश्न, प्रत्येकी २ गुण)
for i in range(1, 15):
    GLOBAL_STRUCTURE.append({"id": f"q1_{i}", "label": f"Q.1 ({i})", "max": 2})

# Q.2 ते Q.6 (प्रत्येकी ४ उपप्रश्न: A, B, C, D - प्रत्येकी ५ गुण)
for q_num in range(2, 7):
    for sub in ['a', 'b', 'c', 'd']:
        GLOBAL_STRUCTURE.append({"id": f"q{q_num}_{sub}", "label": f"Q.{q_num} ({sub.upper()})", "max": 5})

# Q.7 (२ उपप्रश्न - प्रत्येकी १० गुण)
GLOBAL_STRUCTURE.append({"id": "q7_a", "label": "Q.7 (A)", "max": 10})
GLOBAL_STRUCTURE.append({"id": "q7_b", "label": "Q.7 (B)", "max": 10})


@app.route('/')
def index():
    current_paper = request.args.get('paper', '')
    subject_name = request.args.get('subject', 'Basics of Electric Vehicle')
    
    total_max_marks = sum(q['max'] for q in GLOBAL_STRUCTURE)
    db = load_permanent_db()
    
    all_papers = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.pdf')]
    all_papers.sort()
    
    if not current_paper and all_papers:
        current_paper = all_papers[0]
    elif not current_paper:
        current_paper = 'sample.pdf'
        
    paper_barcode_map = {"sample.pdf": "25493362"}
    if current_paper not in paper_barcode_map:
        current_barcode = str(abs(hash(current_paper)) % 10000000 + 20000000)
    else:
        current_barcode = paper_barcode_map[current_paper]
        
    total_uploaded = len(all_papers) if all_papers else 1
    checked_count = 0
    for paper in all_papers:
        bc = str(abs(hash(paper)) % 10000000 + 20000000) if paper != "sample.pdf" else "25493362"
        if bc in db.get("locked", []):
            checked_count += 1
            
    unchecked_count = total_uploaded - checked_count
    is_locked = "true" if current_barcode in db.get("locked", []) else "false"
    
    paper_data = db.
