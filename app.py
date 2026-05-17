from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def dashboard():
    # This will look for your sample.pdf inside static/answer_sheets/
    return render_template('dashboard.html', paper_file="sample.pdf")

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    if request.method == 'POST':
        # Get marks from the form inputs
        q1 = request.form.get('q1', 0)
        q2 = request.form.get('q2', 0)
        
        # Convert input string values to integers safely
        q1_val = int(q1) if q1 else 0
        q2_val = int(q2) if q2 else 0
        
        total = q1_val + q2_val
        return f"<h3>Marks submitted successfully!<br>Total Marks: {total}</h3> <a href='/'>Go Back</a>"

if __name__ == '__main__':
    app.run(debug=True)