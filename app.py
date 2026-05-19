import os
import json
import io
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

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
    current_paper = request.args.get('paper', 'sample.pdf')
    
    # Matching your exact structural matrix requirements (Q1 through Q7)
    structure = [
        {"id": "q1_1", "label": "Q.1 (1)", "max": 1},
        {"id": "q1_2", "label": "Q.1 (2)", "max": 1},
        {"id": "q1_3", "label": "Q.1 (3)", "max": 1},
        {"id": "q1_4", "label": "Q.1 (4)", "max": 1},
        {"id": "q1_5", "label": "Q.1 (5)", "max": 1},
        {"id": "q1_6", "label": "Q.1 (6)", "max": 2},
        {"id": "q1_7", "label": "Q.1 (7)", "max": 2},
        {"id": "q1_8", "label": "Q.1 (8)", "max": 2},
        {"id": "q2_a", "label": "Q.2 (A)", "max": 5},
        {"id": "q2_b", "label": "Q.2 (B)", "max": 5},
        {"id": "q2_c", "label": "Q.2 (C)", "max": 5},
        {"id": "q3_a", "label": "Q.3 (A)", "max": 5},
        {"id": "q3_b", "label": "Q.3 (B)", "max": 5},
        {"id": "q4_c", "label": "Q.4 (C)", "max": 5},
        {"id": "q4_d", "label": "Q.4 (D)", "max": 5},
        {"id": "q5_a", "label": "Q.5 (A)", "max": 5},
        {"id": "q5_b", "label": "Q.5 (B)", "max": 5},
        {"id": "q5_c", "label": "Q.5 (C)", "max": 5},
        {"id": "q5_d", "label": "Q.5 (D)", "max": 5},
        {"id": "q6_a", "label": "Q.6 (A)", "max": 5},
        {"id": "q6_b", "label": "Q.6 (B)", "max": 5},
        {"id": "q6_c", "label": "Q.6 (C)", "max": 5},
        {"id": "q6_d", "label": "Q.6 (D)", "max": 5},
        {"id": "q7_a", "label": "Q.7 (A)", "max": 10},
        {"id": "q7_b", "label": "Q.7 (B)", "max": 10}
    ]
    
    total_max = sum(q["max"] for q in structure)
    db = load_permanent_db()
    
    # Synchronizing barcodes dynamically based on chosen file status parameters
    barcode = "29008603" if "Fm" in current_paper else "25493362"
    
    saved_scores = db.get("data", {}).get(barcode, {}).get("scores", {})
    saved_stamps = db.get("data", {}).get(barcode, {}).get("stamps", [])
    is_locked = "true" if barcode in db.get("locked", []) else "false"
    
    return render_template(
        'dashboard.html',
        subject_name=subject_name,
        current_paper=current_paper,
        barcode=barcode,
        total_uploaded=2,
        checked_count=len(db.get("locked", [])),
        unchecked_count=max(0, 2 - len(db.get("locked", []))),
        all_papers=['sample.pdf', 'Fm practical.pdf'],
        structure=structure,
        total_max=total_max,
        saved_scores=saved_scores,
        saved_stamps=json.dumps(saved_stamps),
        is_locked=is_locked
    )

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
    db = load_permanent_db()
    all_data = db.get("data", {})
    
    if not all_data:
        return "No grading entries available to generate Excel spreadsheet sheets!", 400

    rows = []
    for barcode, info in all_data.items():
        row_dict = {
            "Barcode": barcode,
            "Subject": info.get("subject", ""),
            "Paper Name": info.get("paper", ""),
            "Status": "Locked" if barcode in db.get("locked", []) else "Unchecked"
        }
        
        scores = info.get("scores", {})
        for q_id, score in scores.items():
            clean_q_name = q_id.replace("input_", "").upper()
            row_dict[clean_q_name] = score
            
        rows.append(row_dict)

    df = pd.DataFrame(rows)

    def calculate_numeric_total(row):
        total = 0
        for col in df.columns:
            if col not in ["Barcode", "Subject", "Paper Name", "Status"]:
                val = str(row[col]).strip()
                if val == "✔️":
                    total += 1
                elif val == "½":
                    total += 0.5
                elif val.replace('.', '', 1).isdigit():
                    total += float(val)
        return total

    if not df.empty:
        df['GRAND TOTAL'] = df.apply(calculate_numeric_total, axis=1)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Evaluation Report')
    
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="OSM_Final_Report.xlsx"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
