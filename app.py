import os
import csv
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = 'solapur_university_osm_secure_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'answer_sheets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 📊 मास्टर स्ट्रक्चर (Q.1 चे १४ उपप्रश्न आणि Q.2 ते Q.7 मुख्य प्रश्न)
GLOBAL_STRUCTURE = []
for i in range(1, 15):
    GLOBAL_STRUCTURE.append({"id": f"q1_{i}", "label": f"Q.1 ({i})", "max": 2})
for i in range(2, 8):
    GLOBAL_STRUCTURE.append({"id": f"q{i}", "label": f"Q.{i}", "max": 5})

# तात्पुरती मेमरी डेटाबेस (प्रॉडक्शनसाठी तुम्ही ही फाईल marks_database.csv मध्ये सेव्ह करू शकता)
EVALUATION_DATABASE = {}
LOCKED_PAPERS = set()

@app.route('/')
def index():
    current_paper = request.args.get('paper', 'sample.pdf')
    subject_name = request.args.get('subject', 'Basics of Electric Vehicle') #
    
    total_max_marks = sum(q['max'] for q in GLOBAL_STRUCTURE)
    
    paper_barcode_map = {
        "sample.pdf": "25493362",
        "student_02.pdf": "25493363"
    }
    current_barcode = paper_barcode_map.get(current_paper, "25493364")
    is_locked = "true" if current_barcode in LOCKED_PAPERS else "false"

    return render_template('dashboard.html', 
                           current_paper=current_paper, 
                           subject_name=subject_name,
                           structure=GLOBAL_STRUCTURE,
                           total_max=total_max_marks,
                           barcode=current_barcode,
                           is_locked=is_locked)

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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index', paper=filename, subject=subject))
        return "फक्त PDF फाईल्स अपलोड करा", 400
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        data = request.get_json()
        barcode = data['barcode']
        
        # डेटाबेसमध्ये रेकॉर्ड सेव्ह करणे
        EVALUATION_DATABASE[barcode] = {
            "subject": data['subject'],
            "paper": data['paper'],
            "scores": data['scores']
        }
        LOCKED_PAPERS.add(barcode)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 📊 Excel/CSV शीट डाऊनलोड करण्याचा नवीन रूट
@app.route('/export_excel', methods=['POST'])
def export_excel():
    try:
        data = request.get_json()
        barcode = data.get('barcode', '25493362')
        subject = data.get('subject', 'Basics of Electric Vehicle')
        scores = data.get('scores', {})

        # Excel सुसंगत CSV फाईल मेमरीमध्ये तयार करणे
        si = StringIO()
        cw = csv.writer(si)
        
        # हेडर आणि मेटा डेटा
        cw.writerow(['Solapur University - OSM Evaluation Report'])
        cw.writerow([])
        cw.writerow(['Subject Name', subject])
        cw.writerow(['Answer Sheet Barcode', barcode])
        cw.writerow([])
        cw.writerow(['Question Number', 'Obtained Marks'])
        
        # सर्व प्रश्नांचे मार्क्स रो नुसार लिहिणे
        for q_id, mark in scores.items():
            clean_q_name = q_id.replace('q1_', 'Q.1.').replace('q', 'Q.')
            cw.writerow([clean_q_name, mark])
            
        # एकूण गुणांची बेरीज शेवटी जोडणे
        total_score = data.get('total_score', '0')
        cw.writerow([])
        cw.writerow(['Total Matrix Score', total_score])

        output = BytesIO()
        output.write(si.getvalue().encode('utf-8-sig')) # utf-8-sig मुळे Excel मध्ये मराठी/इंग्रजी फॉन्ट व्यवस्थित दिसतात
        output.seek(0)
        
        return send_file(output, 
                         mimetype='text/csv', 
                         as_attachment=True, 
                         download_name=f"Evaluation_Report_{barcode}.csv")
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
