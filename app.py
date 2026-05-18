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

# 📊 नवीन सुधारीत प्रश्न रचना (Q1 ते Q7 पूर्ण मॅट्रिक्स)
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
    
    all_papers = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.pdf') or f.endswith('.png') or f.endswith('.jpg')]
    all_papers.sort()
    
    if not current_paper and all_papers:
        current_paper = all_papers[0]
    elif not current_paper:
        current_paper = 'sample.pdf'
        
    current_barcode = str(abs(hash(current_paper)) % 10000000 + 20000000)
    
    total_uploaded = len(all_papers) if all_papers else 1
    checked_count = len(db.get("locked", []))
    unchecked_count = max(0, total_uploaded - checked_count)
    
    is_locked = "true" if current_barcode in db.get("locked", []) else "false"
    
    paper_data = db.get("data", {}).get(current_barcode, {})
    saved_scores = paper_data.get("scores", {})
    saved_stamps = paper_data.get("stamps", [])

    return render_template('dashboard.html', 
                           current_paper=current_paper, 
                           all_papers=all_papers,
                           subject_name=subject_name,
                           structure=GLOBAL_STRUCTURE,
                           total_max=total_max_marks,
                           barcode=current_barcode,
                           is_locked=is_locked,
                           total_uploaded=total_uploaded,
                           checked_count=checked_count,
                           unchecked_count=unchecked_count,
                           saved_scores=json.dumps(saved_scores),
                           saved_stamps=json.dumps(saved_stamps))

@app.route('/upload_sheet', methods=['POST'])
def upload_sheet():
    try:
        if 'file' not in request.files:
            return "File error", 400
        file = request.files['file']
        subject = request.form.get('subject', 'Basics of Electric Vehicle')
        if file.filename == '':
            return "No file selected", 400
        filename = file.filename.replace(" ", "_")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index', paper=filename, subject=subject))
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        data = request.get_json()
        barcode = data['barcode']
        db = load_permanent_db()
        db["data"][barcode] = {
            "subject": data['subject'],
            "paper": data['paper'],
            "scores": data['scores'],
            "stamps": data.get('stamps', [])
        }
        if barcode not in db["locked"]:
            db["locked"].append(barcode)
        save_permanent_db(db)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/export_excel', methods=['POST'])
def export_excel():
    try:
        data = request.get_json()
        barcode = data.get('barcode', '')
        subject = data.get('subject', '')
        scores = data.get('scores', {})

        si = StringIO()
        cw = csv.writer(si)
        
        # Excel Header Matrix Format
        headers = ['Barcode No', 'Subject Name']
        row_data = [barcode, subject]
        
        for q in GLOBAL_STRUCTURE:
            headers.append(q['label'])
            # जर व्हॅल्यू ✔️ असेल तर मॅक्स मार्क्स टाका, अन्यथा तीच संख्या ठेवा
            mark_val = scores.get(q['id'], '0')
            if mark_val == '✔️':
                mark_val = str(q['max'])
            elif mark_val == '❌':
                mark_val = '0'
            row_data.append(mark_val)
            
        headers.append('Grand Total')
        
        total_columns = len(GLOBAL_STRUCTURE) + 2
        def get_column_letter(n):
            result = ""
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                result = chr(65 + remainder) + result
            return result
            
        last_col_letter = get_column_letter(total_columns - 1)
        row_data.append(f"=SUM(C2:{last_col_letter}2)")
        
        cw.writerow(headers)
        cw.writerow(row_data)

        output = BytesIO()
        output.write(si.getvalue().encode('utf-8-sig'))
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"OSM_Report_{barcode}.csv")
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
