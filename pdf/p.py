from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import os
import requests
from io import BytesIO

# Функция для загрузки шрифта
def register_fonts():
    try:
        # Пытаемся зарегистрировать Arial, если он доступен в системе
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        print("Шрифт Arial зарегистрирован из системных файлов")
    except:
        try:
            # Альтернативный вариант - использовать DejaVu Sans (часто доступен)
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            print("Шрифт DejaVuSans зарегистрирован")
        except:
            try:
                # Если системные шрифты недоступны, скачиваем шрифт
                font_url = "https://github.com/OpenBangla/OpenBangla-Font/raw/master/FreeBengaliFonts/Arial%20Unicode%20MS.ttf"
                response = requests.get(font_url)
                font_data = BytesIO(response.content)
                pdfmetrics.registerFont(TTFont('ArialUnicode', font_data))
                print("Шрифт Arial Unicode загружен и зарегистрирован")
            except Exception as e:
                print(f"Не удалось загрузить шрифт: {e}")
                # Используем стандартный шрифт как запасной вариант
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                # Попробуем использовать любой доступный шрифт
                try:
                    pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/truetype/freefont/FreeSans.ttf'))
                except:
                    print("Используется стандартный шрифт ReportLab")

# Регистрируем шрифты при импорте модуля
register_fonts()

def get_available_font():
    """Определяет доступный шрифт с поддержкой кириллицы"""
    available_fonts = ['Arial', 'DejaVuSans', 'ArialUnicode', 'Helvetica']
    for font_name in available_fonts:
        if pdfmetrics.getFont(font_name):
            return font_name
    return 'Helvetica'  # Стандартный шрифт ReportLab

def addTitle(doc, title, above, under, align=TA_LEFT):
    font_name = get_available_font()
    doc.append(Spacer(1, above))
    doc.append(Paragraph(title, ParagraphStyle(fontName=font_name, fontSize=32, alignment=align)))
    doc.append(Spacer(1, under))
    return doc

def addParagraphs(doc, parts):
    font_name = get_available_font()
    for part in parts:
        doc.append(Paragraph(part, ParagraphStyle(fontName=font_name, fontSize=14, bulletText='•', bulletFontSize=14)))
        doc.append(Spacer(1, 10))
    doc.append(Paragraph('_' * 100, ParagraphStyle(fontName=font_name, fontSize=14)))
    return doc

def addConv1(conv):
    data = []
    if not conv:
        return data
    
    font_name = get_available_font()
    style_assistant = ParagraphStyle(fontName=font_name, fontSize=12, alignment=TA_CENTER)
    style_user = ParagraphStyle(fontName=font_name, fontSize=12, alignment=TA_CENTER)
    
    data.append([Paragraph("Что вас беспокоит?", style_assistant),
                 Paragraph(conv[0]["content"], style_user)])
    
    for k, part in enumerate(conv[1:]):
        if part['role'] == 'assistant':
            a = Paragraph(conv[k+1]["content"], style_assistant)
            try:
                u = Paragraph(conv[k+2]["content"], style_user)
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
    font_name = get_available_font()
    
    # Логотип (обработка ошибок если файла нет)
    try:
        document.append(Image('logo.jpg', 1.6*inch, 1.33*inch))
    except:
        print("Логотип не найден, продолжаем без него")
    
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
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    table.setStyle(style)
    document.append(table)
    return document

# Дополнительная функция для создания PDF файла
def generate_pdf(json_data, output_filename="report.pdf"):
    """Создает PDF файл из JSON данных"""
    document_elements = create_rep(json_data)
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    doc.build(document_elements)
    return output_filename
