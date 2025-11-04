from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json

# Регистрируем шрифт Arial для поддержки кириллицы
pdfmetrics.registerFont(TTFont('Arial', 'ARIAL.ttf'))

def addTitle(doc, title, above, under, align=TA_LEFT):
    doc.append(Spacer(1, above))
    doc.append(Paragraph(title, ParagraphStyle(fontName="Arial", fontSize=32, alignment=align)))
    doc.append(Spacer(1, under))
    return doc

def addParagraphs(doc, parts):
    for part in parts:
        doc.append(Paragraph(part, ParagraphStyle(fontName="Arial", fontSize=14, bulletText='•', bulletFontSize=14)))
        doc.append(Spacer(1, 10))
    doc.append(Paragraph('_' * 100))
    return doc

def addConv1(conv):
    data = []
    if not conv:
        return data
    data.append([Paragraph("Что вас беспокоит?", ParagraphStyle(fontName="Arial", fontSize=12, alignment=TA_CENTER)),
                 Paragraph(conv[0]["content"], ParagraphStyle(fontName="Arial", fontSize=12, alignment=TA_CENTER))])
    for k, part in enumerate(conv[1:]):
        if part['role'] == 'assistant':
            a = Paragraph(conv[k+1]["content"], ParagraphStyle(fontName="Arial", fontSize=12, alignment=TA_CENTER))
            try:
                u = Paragraph(conv[k+2]["content"], ParagraphStyle(fontName="Arial", fontSize=12, alignment=TA_CENTER))
                data.append([a, u])
            except:
                pass
    return data

def create_rep(json_data):
    try:
        conv = json_data[0]['convo']
        diags = json.loads(json_data[1])['potential_diagnosis']
        syms = json.loads(json_data[1])['patient_symptoms']
    except:
        conv, diags, syms = [], [], []

    document = []
    # Логотип
    document.append(Image('logo.jpg', 1.6*inch, 1.33*inch))
    
    # Симптомы
    document = addTitle(document, 'Симптомы', 10, 40)
    document = addParagraphs(document, syms)
    
    # Возможные диагнозы
    document = addTitle(document, 'Возможные диагнозы', 10, 40)
    document = addParagraphs(document, diags)
    
    # Беседа с ботом
    document = addTitle(document, 'Беседа с ботом', 10, 40, TA_CENTER)
    d = addConv1(conv)

    # Таблица диалога
    data = [['Ассистент', 'Пациент']]
    for el in d:
        data.append(el)

    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Arial'),  # Шрифт с поддержкой кириллицы
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    table.setStyle(style)
    document.append(table)
    return document
