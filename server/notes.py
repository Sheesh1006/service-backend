from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from io import BytesIO

pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

class Notes2pdf(object):
    def __init__(self, timestamps: list[str], summary: list[str], video_frames) -> None:
        self.title = self._getTitle(summary)
        self.timestamps = timestamps
        self.summary = summary
        self.video_frames = video_frames
    
    def _getTitle(self, summary: list[str]) -> str:
        if summary:
            raw_title = summary[0]
            words = raw_title.split()
            midpoint = len(words) // 2
            title = " ".join(words[:midpoint])  + " ".join(words[midpoint:])
        else:
            title = "Краткий конспект"
        return title
    
    def _wrap(self, text, width, c, font, size):
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            line = ""
            for word in words:
                if c.stringWidth(line + word + " ", font, size) <= width:
                    line += word + " "
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
        return lines
    
    def _split_title(self, title, max_width, canvas_obj, font_name, font_size):
        words = title.split()
        lines, line = [], ""
        for word in words:
            if canvas_obj.stringWidth(line + word + " ", font_name, font_size) < max_width:
                line += word + " "
            else:
                lines.append(line.strip())
                line = word + " "
        if line:
            lines.append(line.strip())
        return lines
    
    def export_pdf(self):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        x, y = 50, height - 50

        # Заголовок
        c.setFont("DejaVuSans", 18)
        title_lines = self._split_title(self.title, width - 2 * x, c, "DejaVuSans", 18)
        for i, line in enumerate(title_lines):
            c.drawString(x, y - i * 22, line)
        y -= len(title_lines) * 22 + 20

        # План занятия
        c.setFont("DejaVuSans", 14)
        c.drawString(x, y, "План занятия:")
        y -= 20
        c.setFont("DejaVuSans", 12)
        for line in self.timestamps:
            c.drawString(x + 20, y, line)
            y -= 16
        y -= 10

        # Краткое содержание
        c.setFont("DejaVuSans", 14)
        c.drawString(x, y, "Краткое содержание:")
        y -= 20
        c.setFont("DejaVuSans", 12)
        for s in self.summary:
            lines = self._wrap(s, width - 2 * x, c, "DejaVuSans", 12)
            if y < 80:
                c.showPage(); y = height - 50; c.setFont("DejaVuSans", 12)
            if lines:
                c.drawString(x, y, f"• {lines[0]}")
                y -= 18
                for line in lines[1:]:
                    c.drawString(x + 15, y, line)
                    y -= 16
            y -= 10

        # Визуальные материалы (в конце)
        if self.video_frames:
            c.showPage()
            y = height - 50
            c.setFont("DejaVuSans", 14)
            c.drawString(x, y, "Визуальные материалы из видео")
            y -= 30
            for img in self.video_frames:
                try:
                    img_width = 400
                    img_height = 300
                    if y < img_height + 50:
                        c.showPage(); y = height - 50; c.setFont("DejaVuSans", 12)
                    img_reader = ImageReader(img)
                    c.drawImage(img_reader, x, y - img_height, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
                    y -= img_height + 20
                except:
                    continue
        c.save()
        buffer.seek(0)
        return buffer.getvalue()