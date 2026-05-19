import os
import json
import io
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'answer_sheets')
DB_FILE = "permanent_db.json"

def load_permanent_db():
    if not os.path.exists(DB_FILE):
        return {"data": {}, "locked": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"data": {}, "locked": []}

def save_permanent_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

@app.route('/')
def index():
    subject_name = request.args.get('subject', 'Basics of Electric Vehicle')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    try:
        all_papers = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.lower().endswith('.pdf')]
    except Exception:
        all_papers = []
        
    if not all_papers:
        all_papers = ['sample.pdf', 'Fm practical.pdf']
        
    current_paper = request.args.get('paper', all_papers[0])
    
    structure = [
        {"id": "q1_1", "label": "Q.1(1)", "max": 1},
        {"id": "q1_2", "label": "Q.1(2)", "max": 1},
        {"id": "q1_3", "label": "Q.1(3)", "max": 1},
        {"id": "q1_4", "label": "Q.1(4)", "max": 1},
        {"id": "q1_5", "label": "Q.1(5)", "max": 1},
        {"id": "q1_6", "label": "Q.1(6)", "max": 2},
        {"id": "q1_7", "label": "Q.1(7)", "max": 2},
        {"id": "q1_8", "label": "Q.1(8)", "max": 2},
        {"id": "q2_a", "label": "Q.2(a)", "max": 5},
        {"id": "q2_b", "label": "Q.2(b)", "max": 5},
        {"id": "q2_c", "label": "Q.2(c)", "max": 5},
        {"id": "q3_a", "label": "Q.3(a)", "max": 5},
        {"id": "q3_b", "label": "Q.3(b)", "max": 5},
        {"id": "q4_c", "label": "Q.4(c)", "max": 5},
        {"id": "q4_d", "label": "Q.4(d)", "max": 5},
        {"id": "q5_a", "label": "Q.5(a)", "max": 5},
        {"id": "q5_b", "label": "Q.5(b)", "max": 5},
        {"id": "q5_c", "label": "Q.5(c)", "max": 5},
        {"id": "q5_d", "label": "Q.5(d)", "max": 5},
        {"id": "q6_a", "label": "Q.6(a)", "max": 5},
        {"id": "q6_b", "label": "Q.6(b)", "max": 5},
        {"id": "q6_c", "label": "Q.6(c)", "max": 5},
        {"id": "q6_d", "label": "Q.6(d)", "max": 5},
        {"id": "q7_a", "label": "Q.7(a)", "max": 10},
        {"id": "q7_b", "label": "Q.7(b)", "max": 10}
    ]
    
    total_max = sum(q["max"] for q in structure)
    db = load_permanent_db()
    
    barcode = "29008603" if "Fm" in current_paper else "25493362"
    
    saved_scores = db.get("data", {}).get(barcode, {}).get("scores", {})
    saved_stamps = db.get("data", {}).get(barcode, {}).get("stamps", [])
    is_locked = "true" if barcode in db.get("locked", []) else "false"
    
    return render_template(
        'dashboard.html',
        subject_name=subject_name,
        current_paper=current_paper,
        barcode=barcode,
        total_uploaded=len(all_papers),
        checked_count=len(db.get("locked", [])),
        unchecked_count=max(0, len(all_papers) - len(db.get("locked", []))),
        all_papers=all_papers,
        structure=structure,
        total_max=total_max,
        saved_scores=saved_scores,
        saved_stamps=json.dumps(saved_stamps),
        is_locked=is_locked
    )

@app.route('/upload_sheet', methods=['POST'])
def upload_sheet():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    subject = request.form.get('subject', 'Basics of Electric Vehicle')
    if file and file.filename.lower().endswith('.pdf'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index', paper=filename, subject=subject))
    return redirect(url_for('index'))

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        data = request.get_json()
        barcode = str(data['barcode'])
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

@app.route('/download_excel')
def download_excel():
    try:
        import pandas as pd
    except ImportError:
        return "Pandas library error on server", 500
        
    db = load_permanent_db()
    all_data = db.get("data", {})
    if not all_data:
        return "No records found.", 400

    rows = []
    for barcode, info in all_data.items():
        row_dict = {"Barcode": barcode, "Subject": info.get("subject", ""), "Paper Name": info.get("paper", ""), "Status": "Locked" if barcode in db.get("locked", []) else "Unchecked"}
        scores = info.get("scores", {})
        for q_id, score in scores.items():
            row_dict[q_id.replace("input_", "").upper()] = score
        rows.append(row_dict)

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Evaluation Report')
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="OSM_Final_Report.xlsx")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
