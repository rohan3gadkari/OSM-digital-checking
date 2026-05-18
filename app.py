from flask import Flask, render_template, request, jsonify
import csv
import os

app = Flask(__name__)

# Excel (CSV) फाईलचा पाथ सेट करणे
DATABASE_FILE = 'marks_database.csv'

# जर फाईल आधीपासून नसेल, तर हेडर तयार करणे
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Paper File', 'Question 1', 'Question 2', 'Total Marks'])

@app.route('/')
def dashboard():
    return render_template('dashboard.html', paper_file="sample.pdf")

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        # AJAX कडून आलेला डेटा मिळवणे
        data = request.get_json()
        paper_file = data.get('paper_file', 'unknown.pdf')
        q1 = int(data.get('q1', 0))
        q2 = int(data.get('q2', 0))
        total = q1 + q2

        # डेटा Excel (CSV) फाईलमध्ये सेव्ह करणे
        with open(DATABASE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([paper_file, q1, q2, total])

        # ब्राउझरला यशस्वी झाल्याचा मेसेज पाठवणे
        return jsonify({'status': 'success', 'total': total})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
