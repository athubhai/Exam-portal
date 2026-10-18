import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

doc = docx.Document()

# Page Margins
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Read Markdown
with open('REVIEW_2_IMPLEMENTATION_AND_RESULTS.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_code_block = False
code_lines = []
in_table = False
table_lines = []

def process_table(tbl_lines):
    rows = []
    for line in tbl_lines:
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if all(set(p).issubset({'-', ':', ' '}) for p in parts if p):
            continue
        rows.append(parts)
    if not rows:
        return
    num_cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(rows):
        for c_idx, cell_text in enumerate(row):
            if c_idx < num_cols:
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_text
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                for run in p.runs:
                    run.font.size = Pt(8.5)
                    run.font.name = 'Calibri'
                    if r_idx == 0:
                        run.bold = True
                if r_idx == 0:
                    set_cell_background(cell, '1F2937')
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(255, 255, 255)
                elif r_idx % 2 == 1:
                    set_cell_background(cell, 'F9FAFB')

for line in lines:
    stripped = line.strip()
    
    if stripped.startswith('`'):
        if in_code_block:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run('\n'.join(code_lines))
            run.font.name = 'Consolas'
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(30, 41, 59)
            code_lines = []
            in_code_block = False
        else:
            in_code_block = True
            code_lines = []
        continue
    
    if in_code_block:
        code_lines.append(line.rstrip('\r\n'))
        continue
        
    if stripped.startswith('|') and stripped.endswith('|'):
        in_table = True
        table_lines.append(stripped)
        continue
    else:
        if in_table:
            process_table(table_lines)
            table_lines = []
            in_table = False
            
    if not stripped or stripped == '---':
        continue
        
    if stripped.startswith('# '):
        h = doc.add_heading(stripped[2:], level=0)
        h.paragraph_format.space_after = Pt(6)
    elif stripped.startswith('## '):
        h = doc.add_heading(stripped[3:], level=1)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
    elif stripped.startswith('### '):
        h = doc.add_heading(stripped[4:], level=2)
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(3)
    elif stripped.startswith('#### '):
        h = doc.add_heading(stripped[5:], level=3)
        h.paragraph_format.space_before = Pt(6)
        h.paragraph_format.space_after = Pt(2)
    elif stripped.startswith('* ') or stripped.startswith('- '):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.add_run(stripped[2:])
    elif any(stripped.startswith(f'{i}. ') for i in range(1, 10)):
        p = doc.add_paragraph(style='List Number')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        idx = stripped.find('. ')
        p.add_run(stripped[idx+2:])
    else:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        p.add_run(stripped)

if in_table:
    process_table(table_lines)

doc.save('REVIEW_2_IMPLEMENTATION_AND_RESULTS.docx')
print('Successfully generated REVIEW_2_IMPLEMENTATION_AND_RESULTS.docx')
