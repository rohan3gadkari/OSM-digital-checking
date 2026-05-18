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

# 📊 Q.1 ते Q.7 मार्किंग मॅट्रिक्स रचना (सर्व उपप्रश्नांसह)
GLOBAL_STRUCTURE = []

# Q.1 (Objective - ९ उपप्रश्न, प्रत्येकी २ गुण)
for i in range(1, 10):
    GLOBAL_STRUCTURE.append({"id": f"q1_{i}", "label": f"Q.1 ({i})", "max": 2})

# Q.2 ते Q.6 (प्रत्येकी ४ उपप्रश्न, ५ गुण)
for q_num in range(2, 7):
    for sub in ['a', 'b', 'c', 'd']:
        GLOBAL_STRUCTURE.append({"id": f"q{q_num}_{sub}", "label": f"Q.{q_num} ({sub.upper()})", "max": 5})

# Q.7 (दीर्घोत्तरी प्रश्न - २ उपप्रश्न, प्रत्येकी १० गुण)
GLOBAL_STRUCTURE.append({"id": "q7_a", "label": "Q.7 (A)", "max": 10})
GLOBAL_STRUCTURE.append({"id": "q7_b", "label": "Q.7 (B)", "max": 10})


@app.route('/')
def index():
    current_paper = request.args.get('paper', '')
    subject_name = request.args.get('subject', 'Basics of Electric Vehicle')
    
    total_max_marks = sum(q['max'] for q in GLOBAL_STRUCTURE)
    db = load_permanent_db()
    
    # 📂 डिरेक्टरीमधून सर्व अपलोड केलेल्या PDF फाइल्सची लिस्ट काढणे
    all_papers = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.pdf')]
    all_papers.sort()
    
    # जर कोणतीही फाईल निवडली नसेल तर पहिली फाईल दाखवणे
    if not current_paper and all_papers:
        current_paper = all_papers[0]
    elif not current_paper:
        current_paper = 'sample.pdf' # Default backup
        
    # बारकोड मॅपिंग आणि जनरेशन
    paper_barcode_map = {"sample.pdf": "25493362"}
    if current_paper not in paper_barcode_map:
        current_barcode = str(abs(hash(current_paper)) % 10000000 + 20000000)
    else:
        current_barcode = paper_barcode_map[current_paper]
        
    # 📊 लाइव्ह काउंटर कॅल्क्युलेशन (Checked vs Not Checked)
    total_uploaded = len(all_papers) if all_papers else 1
    checked_count = 0
    
    for paper in all_papers:
        bc = str(abs(hash(paper)) % 10000000 + 20000000) if paper != "sample.pdf" else "25493362"
        if bc in db.get("locked", []):
            checked_count += 1
            
    unchecked_count = total_uploaded - checked_count
    
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
            return "फाईल सापडली नाही", 400
        file = request.files['file']
        subject = request.form.get('subject', 'Basics of Electric Vehicle')
        
        if file.filename == '':
            return "कोणतीही फाईल निवडलेली नाही", 400
            
        if file and file.filename.endswith('.pdf'):
            filename = file.filename.replace(" ", "_")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            return redirect(url_for('index', paper=filename, subject=subject))
        return "फक्त PDF फाईल्स अपलोड करा", 400
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


# ========================================================
# 📊 EXCEL (CSV FORMAT) GENERATION ROUTE (नवीन सुरक्षित मार्ग)
# ========================================================
@app.route('/download_excel')
def download_excel():
    try:
        db = load_permanent_db()
        all_data = db.get("data", {})
        
        if not all_data:
            return "<h3>कोणताही डेटा उपलब्ध नाही! आधी किमान एका पेपरचे मार्क्स तपासून 'Final Save & Submit' करा.</h3>", 400
            
        # Excel कॉलम्स तयार करणे
        headers = ["Barcode", "Subject", "Paper Name", "Status"]
        for q in GLOBAL_STRUCTURE:
            headers.append(q["label"])
            
        # मेमरीमध्ये CSV तयार करणे
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(headers)
        
        # विद्यार्थ्यांचा डेटा भरणे
        for barcode, details in all_data.items():
            status = "Locked & Verified" if barcode in db.get("locked", []) else "Draft"
            row = [
                barcode,
                details.get("subject", ""),
                details.get("paper", ""),
                status
            ]
            
            scores = details.get("scores", {})
            for q in GLOBAL_STRUCTURE:
                q_id = q["id"]
                val = scores.get(q_id, "0")
                
                # ✔️ आणि ❌ चे मार्क्समध्ये रुपांतर करणे
                if val == "✔️":
                    row.append(q["max"])
                elif val == "❌":
                    row.append(0)
                else:
                    try:
                        row.append(float(val))
                    except:
                        row.append(val)
                        
            cw.writerow(row)
            
        output = BytesIO()
        output.write(si.getvalue().encode('utf-8-sig')) # utf-8-sig मुळे मराठी आणि इंग्रजी अक्षरे एक्सलमध्ये व्यवस्थित दिसतात
        output.seek(0)
        
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="OSM_Evaluated_Marks.csv"
        )
        
    except Exception as e:
        return f"<h3>Excel Error: {str(e)}</h3>", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
