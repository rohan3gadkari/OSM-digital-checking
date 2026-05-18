import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

app = Flask(__name__)
app.secret_key = 'solapur_university_osm_secure_key'

# 📂 Linux सर्व्हरसाठी सुरक्षित पाथ आर्किटेक्चर
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'answer_sheets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 📊 मास्टर स्ट्रक्चर (Q.1 चे १४ उपप्रश्न आणि Q.2 ते Q.7)
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
    total_max_marks = sum(q['max'] for q in GLOBAL_STRUCTURE)

    paper_barcode_map = {
        "sample.pdf": "25493362",
        "student_02.pdf": "25493363"
    }
    current_barcode = paper_barcode_map.get(current_paper, "25493362")
    is_locked = "true" if current_barcode in LOCKED_PAPERS else "false"

    return render_template('dashboard.html', 
                           current_paper=current_paper, 
                           structure=GLOBAL_STRUCTURE,
                           total_max=total_max_marks,
                           barcode=current_barcode,
                           is_locked=is_locked)

@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
            
        barcode = data['barcode']

        if barcode in LOCKED_PAPERS:
            return jsonify({'status': 'error', 'message': 'हा पेपर आधीच परमनंट लॉक झाला आहे!'}), 400

        incoming_max = data.get('max_limits', {})
        for q in GLOBAL_STRUCTURE:
            if q['id'] in incoming_max:
                q['max'] = int(incoming_max[q['id']])

        EVALUATION_DATABASE.append({
            "barcode": barcode,
            "paper": data['paper'],
            "scores": data['scores'],
            "max_limits": incoming_max
        })
        
        LOCKED_PAPERS.add(barcode)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download_excel')
def download_excel():
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Final Evaluation Sheet"
        ws.views.sheetView[0].showGridLines = True

        font_title = Font(name="Segoe UI", size=14, bold=True, color="1E293B")
        font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        font_data = Font(name="Segoe UI", size=11)
        fill_header = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        border_thin = Border(left=Side(style='thin', color='CBD5E1'), right=Side(style='thin', color='CBD5E1'),
                             top=Side(style='thin', color='CBD5E1'), bottom=Side(style='thin', color='CBD5E1'))

        ws['A1'] = "Punyashlok Ahilyadevi Holkar Solapur University - Evaluation Database"
        ws['A1'].font = font_title
        ws.row_dimensions[1].height = 25

        headers = ["BarCode No.", "Paper File", "Status Lock"]
        for q in GLOBAL_STRUCTURE:
            headers.append(f"{q['label']}\n[Max: {q['max']}]")
        headers.append("Grand Total")

        ws.row_dimensions[3].height = 35
        for col_idx, text in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_idx, value=text)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_thin

        current_row = 4
        for record in EVALUATION_DATABASE:
            ws.row_dimensions[current_row].height = 22
            sc = record['scores']
            
            ws.cell(row=current_row, column=1, value=record['barcode']).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(row=current_row, column=2, value=record['paper']).alignment = Alignment(horizontal="left", vertical="center")
            
            status_cell = ws.cell(row=current_row, column=3, value="PERMANENT LOCKED")
            status_cell.font = Font(name="Segoe UI", size=10, bold=True, color="B91C1C")
            status_cell.alignment = Alignment(horizontal="center", vertical="center")
            
            c_idx = 4
            for q in GLOBAL_STRUCTURE:
                ws.cell(row=current_row, column=c_idx, value=sc.get(q['id'], 0))
                c_idx += 1
                
            last_col_letter = get_column_letter(c_idx - 1)
            total_formula = f"=SUM(D{current_row}:{last_col_letter}{current_row})"
            
            total_cell = ws.cell(row=current_row, column=c_idx, value=total_formula)
            total_cell.font = Font(name="Segoe UI", bold=True, color="047857")
            total_cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
            
            for c in range(1, c_idx + 1):
                cell = ws.cell(row=current_row, column=c)
                if c >= 4 or c == 1: cell.alignment = Alignment(horizontal="center", vertical="center")
                if c != c_idx and c != 3: cell.font = font_data
                cell.border = border_thin
                
            current_row += 1

        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = 11
        ws.column_dimensions['A'].width = 16
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 20

        # Render सर्व्हरसाठी तात्पुरता सुरक्षित एक्सेल पाथ
        excel_path = os.path.join(BASE_DIR, "OSM_Final_Evaluation_Report.xlsx")
        wb.save(excel_path)
        return send_file(excel_path, as_attachment=True, download_name="OSM_Final_Evaluation_Report.xlsx")
    except Exception as e:
        return f"एक्सेल जनरेशन एरर: {str(e)}", 500

if __name__ == '__main__':
    # लोकल डेव्हलपमेंटसाठी पोर्ट ५०००, सर्व्हरसाठी डायनॅमिक पोर्ट
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
