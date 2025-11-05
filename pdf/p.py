from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import os
import requests
from io import BytesIO

# Функция для регистрации шрифтов с поддержкой кириллицы
def register_cyrillic_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    try:
        # Пытаемся зарегистрировать DejaVu Sans - часто доступен в Linux системах
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        return 'DejaVuSans'
    except:
        try:
            # Пытаемся использовать системный Arial
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            return 'Arial'
        except:
            try:
                # Альтернатива - скачать шрифт с поддержкой кириллицы
                font_url = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Regular.ttf"
                response = requests.get(font_url)
                font_data = BytesIO(response.content)
                pdfmetrics.registerFont(TTFont('Roboto', font_data))
                return 'Roboto'
            except:
                # Запасной вариант - использовать стандартный Helvetica (ограниченная поддержка кириллицы)
                print("Внимание: Используется стандартный шрифт Helvetica. Поддержка кириллицы может быть ограничена.")
                return 'Helvetica'

# Регистрируем шрифты при импорте
CYRILLIC_FONT = register_cyrillic_fonts()

def addTitle(doc, title, above, under, align=TA_LEFT):
    """Добавляет заголовок в документ"""
    doc.append(Spacer(1, above))
    doc.append(Paragraph(title, ParagraphStyle(
        fontName=CYRILLIC_FONT, 
        name='TitleStyle', 
        fontSize=32, 
        alignment=align,
        leading=36  # Межстрочный интервал
    )))
    doc.append(Spacer(1, under))
    return doc

def addParagraphs(doc, parts):
    """Добавляет параграфы с маркерами в документ"""
    for part in parts:
        doc.append(Paragraph(
            part, 
            ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='BulletStyle', 
                fontSize=14, 
                bulletText='•',
                bulletFontSize=14,
                leading=18,  # Межстрочный интервал
                spaceAfter=10
            )
        ))
        doc.append(Spacer(1, 5))
    
    # Разделительная линия
    doc.append(Paragraph(
        '__________________________________________________________________________________________________',
        ParagraphStyle(
            fontName=CYRILLIC_FONT,
            name='DividerStyle',
            fontSize=10,
            textColor=colors.gray
        )
    ))
    return doc

def addConv1(conv):
    """Формирует данные для таблицы диалога"""
    data = []
    if not conv:
        return data
        
    data.append([
        Paragraph(
            "Какие у вас жалобы?", 
            ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='QuestionStyle', 
                fontSize=12, 
                alignment=TA_CENTER,
                leading=16
            )
        ), 
        Paragraph(
            conv[0]["content"], 
            ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='AnswerStyle', 
                fontSize=12, 
                alignment=TA_CENTER,
                leading=16
            )
        )
    ])
    
    for k, part in enumerate(conv[1:]):
        if part['role'] == 'assistant':
            assistant_style = ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='AssistantStyle', 
                fontSize=12, 
                alignment=TA_CENTER,
                leading=16,
                backColor=colors.lightblue
            )
            
            user_style = ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='UserStyle', 
                fontSize=12, 
                alignment=TA_CENTER,
                leading=16,
                backColor=colors.lightgreen
            )
            
            a = Paragraph(conv[k+1]["content"], assistant_style)
            try:
                u = Paragraph(conv[k+2]["content"], user_style)
                data.append([a, u])
            except IndexError:
                # Если нет ответа пользователя, добавляем пустую ячейку
                data.append([a, Paragraph("", user_style)])
    return data

def create_rep(json_data):
    """Создает отчет на основе JSON данных"""
    try:
        conv = json_data[0]['convo']
        diags = json.loads(json_data[1])['potential_diagnosis']
        syms = json.loads(json_data[1])['patient_symptoms']
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Ошибка при обработке JSON данных: {e}")
        conv, diags, syms = [], [], []

    styles = getSampleStyleSheet()
    document = []
    
    # Добавляем логотип (с обработкой ошибок)
    try:
        document.append(Image('logo.jpg', 1.6*inch, 1.33*inch))
        document.append(Spacer(1, 20))
    except Exception as e:
        print(f"Логотип не найден: {e}")
        # Добавляем заголовок вместо логотипа
        document.append(Paragraph(
            "МЕДИЦИНСКИЙ ОТЧЕТ",
            ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='HeaderStyle',
                fontSize=24,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
        ))
        document.append(Spacer(1, 20))
    
    # Раздел: Симптомы
    document = addTitle(document, 'Симптомы', 10, 40)
    
    if syms:
        document = addParagraphs(document, syms)
    else:
        document.append(Paragraph(
            "Симптомы не указаны",
            ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='NoDataStyle',
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
        ))
        document.append(Spacer(1, 20))
    
    # Раздел: Возможные диагнозы
    document = addTitle(document, 'Возможные диагнозы', 10, 40)
    
    if diags:
        document = addParagraphs(document, diags)
    else:
        document.append(Paragraph(
            "Диагнозы не определены",
            ParagraphStyle(
                fontName=CYRILLIC_FONT,
                name='NoDataStyle',
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
        ))
        document.append(Spacer(1, 20))
    
    # Раздел: Беседа с ботом
    document = addTitle(document, 'Беседа с ботом', 10, 40, TA_CENTER)
    
    if conv:
        d = addConv1(conv)
    else:
        d = []

    # Создаем таблицу диалога
    data = [['Ассистент', 'Пациент']]
    
    if d:
        for el in d:
            data.append(el)
    else:
        data.append([
            Paragraph("Данные диалога отсутствуют", 
                     ParagraphStyle(fontName=CYRILLIC_FONT, fontSize=12)),
            Paragraph("Данные диалога отсутствуют", 
                     ParagraphStyle(fontName=CYRILLIC_FONT, fontSize=12))
        ])

    table = Table(data, colWidths=[inch*3, inch*3])
    
    # Стили таблицы с русскими шрифтами
    style = TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    table.setStyle(style)
    document.append(Spacer(1, 20))
    document.append(table)
    
    return document

# Дополнительная функция для удобного создания PDF
def generate_pdf_report(json_data, output_filename="медицинский_отчет.pdf"):
    """
    Генерирует PDF отчет из JSON данных
    """
    try:
        # Создаем элементы документа
        doc_elements = create_rep(json_data)
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title="Медицинский отчет"
        )
        
        # Строим документ
        doc.build(doc_elements)
        print(f"PDF отчет успешно создан: {output_filename}")
        return output_filename
        
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        return None
