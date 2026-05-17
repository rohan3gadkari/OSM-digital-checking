import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Dynamic schema catalog holding custom question patterns
    paper_structures = {
        "mechanical_fluid_mechanics.pdf": [
            {"id": "q1a", "label": "Q1 (a)", "max": 5},
            {"id": "q1b", "label": "Q1 (b)", "max": 5},
            {"id": "q2a", "label": "Q2 (a)", "max": 10},
            {"id": "q2b", "label": "Q2 (b)", "max": 10},
            {"id": "q3",  "label": "Q3 (Full)", "max": 20}
        ],
        "civil_som_exam.pdf": [
            {"id": "q1", "label": "Q1", "max": 10},
            {"id": "q2", "label": "Q2", "max": 10},
            {"id": "q3", "label": "Q3", "max": 10},
            {"id": "q4", "label": "Q4", "max": 10}
        ]
    }

    # Fetch targeted file route arguments from URL parameter '?paper='
    current_paper = request.args.get('paper', 'mechanical_fluid_mechanics.pdf')
    
    # Fallback default evaluation list if target file configuration is missing
    active_structure = paper_structures.get(current_paper, [
        {"id": "q1", "label": "Q1", "max": 5},
        {"id": "q2", "label": "Q2", "max": 5},
        {"id": "q3", "label": "Q3", "max": 5},
        {"id": "q4", "label": "Q4", "max": 5}
    ])

    # Compute maximum threshold benchmark automatically
    total_max_marks = sum(q['max'] for q in active_structure)

    return render_template('dashboard.html', 
                           user="Prof. Gadkari", 
                           current_paper=current_paper, 
                           structure=active_structure,
                           total_max=total_max_marks)
