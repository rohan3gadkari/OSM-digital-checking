from flask import Flask, render_template, request, jsonify, redirect, url_for
import csv
import os

app = Flask(__name__)
DATABASE_FILE = 'marks_database.csv'

# सुरवातीला डेटाबेस तयार करणे
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Paper File', 'Q1', 'Q2', 'Q3', 'Q4', 'Total Marks'])

# 'static/answer_sheets' मधील सर्व पेपर्सची यादी मिळवणे
def get_all_papers():
    folder = os.path.join('static', 'answer_sheets')
    if not os.path.exists(folder):
        os.makedirs(folder)
    papers = [f for f in os.listdir(folder) if f.endswith('.pdf')]
    return sorted(papers) if papers else ['sample.pdf']

@app.route('/')
def dashboard():
    papers = get_all_papers()
    current_paper = request.args.get('paper', papers[0])
    return render_template('dashboard.html', current_paper=current_paper)

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
