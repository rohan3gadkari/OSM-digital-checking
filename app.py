import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'solapur_university_osm_secure_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'answer_sheets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# हे फोल्डर नसल्यास तयार करणे
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 📊 मास्टर स्ट्रक्चर (Q.1 चे १४ उपप्रश्न आणि Q.2 ते Q.7 मुख्य प्रश्न)
GLOBAL_STRUCTURE = []
for i in range(1, 15):
    GLOBAL_STRUCTURE.append({"id": f"q1_{i}", "label": f"Q.1 ({i})", "max": 2})
for i in range(2, 8):
    GLOBAL_STRUCTURE.append({"id": f"q{i}", "label": f"Q.{i}", "max": 5})

EVALUATION_DATABASE = []
LOCKED_PAPERS = set()

@app.route('/')
def index():
    current_paper = request.args.get('paper', 'sample.pdf')
    subject_name = request.args.get('subject', 'Basics of Electric Vehicle') # डिफॉल्ट विषय
    
    total_max_marks = sum(q['max'] for q in GLOBAL_STRUCTURE)
    
    # बारकोड मॅपिंग
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
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'कोणतीही फाईल निवडली नाही'}), 400
    
    file = request.files['file']
    subject = request.form.get('subject', 'Advanced Evaluation Workspace')
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'फाईलचे नाव रिकामे आहे'}), 400
        
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # नवीन फाईलसह मुख्य पेजवर रीडायरेक्ट करणे
        return redirect(f"/?paper={filename}&subject={subject}")
        
    return jsonify({'status': 'error', 'message': 'फक्त PDF फाईल्स अपलोड करा'}), 400

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        data = request.get_json()
        barcode = data['barcode']
        if barcode in LOCKED_PAPERS:
            return jsonify({'status': 'error', 'message': 'हा पेपर परमनंट लॉक आहे!'}), 400

        EVALUATION_DATABASE.append(data)
        LOCKED_PAPERS.add(barcode)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
