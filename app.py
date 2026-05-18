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

# 📂 डेटा कायमचा सेव्ह करण्यासाठी JSON फाईल पाथ
DB_FILE = os.path.join(BASE_DIR, 'marks_db.json')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# सुरुवातीला फाईल नसेल तर रिकामी डिक्शनरी तयार करणे
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

# 📊 मास्टर स्ट्रक्चर (Q.1 चे ९ उपप्रश्न)
GLOBAL_STRUCTURE = []
for i in range(1, 10):
    GLOBAL_STRUCTURE.append({"id": f"q1_{i}", "label": f"Q.1 ({i})", "max": 2})

@app.route('/')
def index():
    current_paper = request.args.get('paper', 'sample.pdf')
    subject_name = request.args.get('subject', 'Basics of Electric Vehicle')
    
    total_max_marks = sum(q['max'] for q in GLOBAL_STRUCTURE)
    
    paper_barcode_map = {
        "sample.pdf": "25493362",
        "ANSWER_SHEET_NO.pdf": "25493363"
    }
    
    if current_paper not in paper_barcode_map:
        # बारकोड फिक्स ठेवण्यासाठी फाईलनेमवरून हॅश कोड जनरेट करणे (दरवेळी बदलणार नाही)
        current_barcode = str(abs(hash(current_paper)) % 10000000 + 20000000)
    else:
        current_barcode = paper_barcode_map[current_paper]
        
    db = load_permanent_db()
    is_locked = "true" if current_barcode in db.get("locked", []) else "false"
    
    # आधीचे सेव्ह केलेले मार्क्स जर असतील तर ते फ्रंटएंडला पाठवणे
    saved_scores = db.get("data", {}).get(current_barcode, {}).get("scores", {})

    return render_template('dashboard.html', 
                           current_paper=current_paper, 
                           subject_name=subject_name,
                           structure=GLOBAL_STRUCTURE,
                           total_max=total_max_marks,
                           barcode=current_barcode,
                           is_locked=is_locked,
                           saved_scores=json.dumps(saved_scores))

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
        
        # डेटा कायमचा फाईलमध्ये सेव्ह करणे
        db["data"][barcode] = {
            "subject": data['subject'],
            "paper": data['paper'],
            "scores": data['scores'],
            "stamps": data.get('stamps', []) # स्टँप्सचे कोऑर्डिनेट्स सेव्ह करणे
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
        barcode = data.get('barcode', '25493362')
        subject = data.get('subject', 'Basics of Electric Vehicle')
        scores = data.get('scores', {})

        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Solapur University - OSM Evaluation Report'])
        cw.writerow([])
        cw.writerow(['Subject Name', subject])
        cw.writerow(['Answer Sheet Barcode', barcode])
        cw.writerow([])
        cw.writerow(['Question Number', 'Obtained Marks'])
        
        for q_id, mark in scores.items():
            clean_q_name = q_id.replace('q1_', 'Q.1.').replace('q', 'Q.')
            cw.writerow([clean_q_name, mark])
            
        total_score = data.get('total_score', '0')
        cw.writerow([])
        cw.writerow(['Total Matrix Score', total_score])

        output = BytesIO()
        output.write(si.getvalue().encode('utf-8-sig'))
        output.seek(0)
        
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"OSM_Report_{barcode}.csv")
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
