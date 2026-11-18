"""Create the two-page portfolio case study with ReportLab."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT=Path(__file__).resolve().parents[1]

def main():
    target=ROOT/'docs/business_case.pdf'
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodySmall',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=7,textColor=colors.HexColor('#21343D')))
    styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8,leading=10,spaceAfter=2))
    styles['Title'].fontSize=22;styles['Title'].leading=26;styles['Title'].alignment=0
    styles['Heading2'].fontSize=12;styles['Heading2'].textColor=colors.HexColor('#116B83')
    story=[]
    def p(text,style='BodySmall'):return Paragraph(text,styles[style])
    def add(text,style='BodySmall'):story.append(p(text,style))
    add('Delivery performance and<br/>customer experience','Title')
    add('BUSINESS ANALYST CASE STUDY - 19 NOVEMBER 2026')
    add('Historical Brazilian Olist commercial data, 2016-2018. Values are BRL. The portfolio does not represent current Australian market conditions.')
    add('Problem and intended users','Heading2')
    add('Operations needs to identify concentrations of late deliveries, understand their association with reviews and allocate investigation effort. Commercial reporting covers 96,478 delivered orders. Delay metrics cover 96,470 orders with both delivery dates.')
    add('<b>Case-study assumptions:</b> an operations manager reviews delivery priorities, seller support investigates seller patterns, customer support communicates with customers, and an analyst reconciles metrics. No stakeholder interviews occurred. Staffing and process needs are proposed.')
    add('Five dashboard requirements and acceptance criteria','Heading2')
    rows=[['ID / requirement','Acceptance criteria'],
        ['R1 - Commercial overview','96,478 delivered orders; BRL 13,221,498.11 merchandise; BRL 2,198,275.64 freight; BRL 137.04 AOV. Monthly totals reconcile to SQL. Sparse and partial coverage is labelled.'],
        ['R2 - Filter delivery results','Month and category filters update page metrics. Overall: 96,470 eligible, 6,534 late, 6.77%. Eight missing-date delivered orders leave the delay denominator. Empty denominators produce blanks.'],
        ['R3 - Compare sellers fairly','Show eligible count, late count and rate. Suppress rate below 100 eligible orders after filters. Seller example: 389 eligible / 74 late = 19.02%. Whole-order association and overlapping counts are disclosed.'],
        ['R4 - Compare review outcomes','One latest valid review per order. On-time/late means 4.29 / 2.27; low-review rates 9.27% / 62.40%. Show coverage and timing limitations. Missing reviews remain missing.'],
        ['R5 - Prioritise by scale and rate','Show SP: 1,820 / 40,494 and RJ: 1,495 / 12,350 late/eligible. Keep Unknown categories. Historical queue reports investigation count, precision, recall and investigations per late order.']]
    table=Table([[p(c,'Cell') for c in row] for row in rows],colWidths=[125,386],hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E4F0F3')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#CAD7DB')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(table)
    story.append(Spacer(1,10))
    add('<b>Acceptance status:</b> source totals and five SQL exports reconcile to pandas. Power BI source passes public JSON schemas. Desktop refresh, DAX and interactive acceptance remain pending because Computer Use failed to start.')
    story.append(PageBreak())
    add('Proposed process and decisions','Title')
    add('PROCESS MAPS ARE CASE-STUDY ASSUMPTIONS')
    add('Current process','Heading2')
    add('Order approval &gt; seller preparation &gt; carrier transit &gt; customer receipt or complaint &gt; reactive support investigation &gt; fragmented issue records.')
    add('Improved process','Heading2')
    add('Order approval &gt; approval-time risk estimate &gt; capacity-limited investigation &gt; verified seller/route check &gt; customer communication &gt; action/outcome log &gt; workload and feedback review.')
    add('Risk triage supports human investigation. A prediction does not prevent a delay, and Olist cannot supply a live queue or prove the proposed process works. Operational implementation needs shipment events and staff capacity absent from this source.')
    add('Three evidence-based recommendations','Heading2')
    add('<b>1. Investigate RJ routes and promise windows, then BA.</b> RJ has 1,495 late orders and a 12.11% rate versus 6.77% overall. BA has 396 late orders at 12.16%. Compare purchase months and route/seller mix before assigning responsibility. SP remains a workload priority with 1,820 late orders despite a 4.49% rate.')
    add('<b>2. Pilot proactive customer communication.</b> Among reviewed eligible orders, 62.40% of late orders receive scores 1-2 versus 9.27% on time. Test communication with a controlled comparison of low-review rate, contacts per order and response coverage. This association does not prove communication will improve reviews.')
    add('<b>3. Pilot capacity-limited approval-time investigation.</b> The validation-selected logistic model finds 124 of 599 late orders by investigating 1,255 test orders: 9.88% precision, 20.70% recall and 10.12 investigations per late order. Random ranking would identify about 60 in expectation. Agree staff capacity and validate a later cohort before deployment.')
    add('Model and evidence limits','Heading2')
    add('Train on earlier approvals, validate January-June 2018, test July-August 2018. Purge training/validation outcomes unavailable at the next boundary. Features exclude delivery outcomes and reviews. Availability of price, freight and static product/location attributes at approval is an assumption. The model covers delivered, observable outcomes and may suffer selection and cohort-follow-up bias.')
    add('The frozen validation threshold flags 31.95% of test orders despite approximately 10% in validation. Monitor workload, precision, recall and geographic burden. No measured delay reduction, financial benefit or deployment readiness is claimed. Review creation can precede final delivery; feedback comparisons are not all post-delivery evaluations.')
    add('Sources and reproducibility','Heading2')
    add('Olist Brazilian E-commerce Public Dataset, Kaggle: kaggle.com/datasets/olistbr/brazilian-ecommerce. Repository evidence: docs/analysis.md; docs/analysis_checks.json; docs/model_audit.json; notebooks/late_delivery_prediction.ipynb; SQL validation and saved exports. Source data and detailed calculations remain inspectable locally. No ROI is estimated because costs and intervention effectiveness are unknown.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#51666E'))
        canvas.drawString(42,25,'Olist portfolio case study - historical Brazil - proposed stakeholder/process assumptions')
        canvas.drawRightString(A4[0]-42,25,str(doc.page))
    SimpleDocTemplate(str(target),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
    from pypdf import PdfReader
    assert len(PdfReader(target).pages)==2, 'Business case must be exactly two pages'
    print('Created two-page case study:',target)

if __name__=='__main__':main()
