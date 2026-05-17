import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# PDF फाईल्स सेव्ह करण्यासाठी फोल्डर
UPLOAD_FOLDER = os.path.join('static', 'answer_sheets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def dashboard():
    # 📊 तुमच्या गरजेनुसार 'sample.pdf' साठी Q.1 a ते Q.5 सेट केले आहे
    paper_structures = {
        "sample.pdf": [
            {"id": "q1a", "label": "Q.1 a", "max": 5},
            {"id": "q2",  "label": "Q.2",   "max": 5},
            {"id": "q3",  "label": "Q.3",   "max": 5},
            {"id": "q4",  "label": "Q.4",   "max": 5},
            {"id": "q5",  "label": "Q.5",   "max": 5}
        ]
    }

    current_paper = request.args.get('paper', 'sample.pdf')
    active_structure = paper_structures.get(current_paper, [
        {"id": "q1", "label": "Q1", "max": 5},
        {"id": "q2", "label": "Q2", "max": 5},
        {"id": "q3", "label": "Q3", "max": 5},
        {"id": "q4", "label": "Q4", "max": 5}
    ])

    total_max_marks = sum(q['max'] for q in active_structure)

    return render_template('dashboard.html', 
                           user="Prof. Gadkari", 
                           current_paper=current_paper, 
                           structure=active_structure,
                           total_max=total_max_marks)

@app.route('/upload_paper', methods=['POST'])
def upload_paper():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file found'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return jsonify({'status': 'success', 'filename': file.filename})
    return jsonify({'status': 'error', 'message': 'Only PDF uploads allowed'}), 400

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    data = request.get_json()
    print("Received Data:", data)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
