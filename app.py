from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import csv
import os

app = Flask(__name__)
DATABASE_FILE = 'marks_database.csv'
UPLOAD_FOLDER = os.path.join('static', 'answer_sheets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# सुरवातीला डेटाबेस आणि अपलोड फोल्डर तयार करणे
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Paper File', 'Q1', 'Q2', 'Q3', 'Q4', 'Total Marks'])

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_all_papers():
    papers = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return sorted(papers) if papers else ['sample.pdf']

@app.route('/')
def dashboard():
    papers = get_all_papers()
    current_paper = request.args.get('paper', papers[0])
    # जर युआरएल मधला पेपर उपलब्ध नसेल तर पहिला पेपर दाखवणे
    if current_paper not in papers:
        current_paper = papers[0]
    return render_template('dashboard.html', current_paper=current_paper)

# 📁 नवीन PDF फाईल अपलोड स्वीकारणारा बॅकएंड रूट
@app.route('/upload_paper', methods=['POST'])
def upload_paper():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'कोणतीही फाईल सापडली नाही!'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'फाईल सिलेक्ट केलेली नाही!'}), 400
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({
            'status': 'success', 
            'message': 'उत्तरपत्रिका यशस्वीरीत्या अपलोड झाली!',
            'filename': filename
        })
    
    return jsonify({'status': 'error', 'message': 'फक्त .pdf फाईल्स अपलोड करण्याची परवानगी आहे!'}), 400

@app.route('/navigate')
def navigate():
    current = request.args.get('current')
    direction = request.args.get('direction')
    papers = get_all_papers()
    
    if current in papers:
        idx = papers.index(current)
        if direction == 'next' and idx < len(papers) - 1:
            idx += 1
        elif direction == 'prev' and idx > 0:
            idx -= 1
        return redirect(url_for('dashboard', paper=papers[idx]))
    return redirect(url_for('dashboard'))

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        data = request.get_json()
        paper_file = data.get('paper_file')
        q1 = int(data.get('q1', 0))
        q2 = int(data.get('q2', 0))
        q3 = int(data.get('q3', 0))
        q4 = int(data.get('q4', 0))
        total = q1 + q2 + q3 + q4

        with open(DATABASE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([paper_file, q1, q2, q3, q4, total])

        return jsonify({'status': 'success', 'total': total})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
