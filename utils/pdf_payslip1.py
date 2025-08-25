from fpdf import FPDF
from datetime import datetime, date
import calendar
import os
import re

FONT_PATH = "fonts"
FONT_NAME = "DejaVu"

class PayslipPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=10)
        self.add_font(FONT_NAME, "", os.path.join(FONT_PATH, "DejaVuSans.ttf"), uni=True)
        self.add_font(FONT_NAME, "B", os.path.join(FONT_PATH, "DejaVuSans-Bold.ttf"), uni=True)
        self.add_font(FONT_NAME, "I", os.path.join(FONT_PATH, "DejaVuSans-Oblique.ttf"), uni=True)
        self.set_font(FONT_NAME, "", 11)
        self.add_page()

    def header(self):
        self.set_font(FONT_NAME, "B", 13)
        self.cell(0, 8, "Shri Swami Samarth Pvt. Ltd.", ln=True, align="C")
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def add_title(self, name, emp_id, month_str):
        self.set_font(FONT_NAME, "", 11)
        self.cell(0, 8, f"Payslip for {name} ({emp_id}) {month_str}", ln=True, align="C")
        self.ln(3)

    def add_attendance_calendar(self, year, month, attendance_map, holidays=[]):
        self.set_font(FONT_NAME, "B", 10)
        self.set_fill_color(230, 230, 255)
        self.cell(0, 7, f"Attendance Overview – {calendar.month_name[month]} {year}", ln=True, fill=True)
        self.set_font(FONT_NAME, "", 9)
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.set_fill_color(240, 240, 240)
        for day in weekdays:
            self.cell(27, 6, txt=day, border=1, align="C", fill=True)
        self.ln()

        first_weekday, total_days = calendar.monthrange(year, month)
        current_day = 1
        row_toggle = False

        while current_day <= total_days:
            self.set_fill_color(255, 255, 255) if row_toggle else self.set_fill_color(245, 245, 245)
            for weekday in range(7):
                if (current_day == 1 and weekday < first_weekday) or current_day > total_days:
                    self.cell(27, 6, txt="", border=1)
                else:
                    dt = date(year, month, current_day)
                    marker = attendance_map.get(current_day)
                    if not marker:
                        marker = "-" if dt.weekday() in [1, 6] or dt.isoformat() in holidays else "A"
                    label = f"{str(current_day).zfill(2)} {marker}"
                    self.cell(27, 6, txt=label, border=1, align="C", fill=True)
                    current_day += 1
            row_toggle = not row_toggle
            self.ln()

        self.ln(2)
        self.set_font(FONT_NAME, "I", 8.5)
        self.multi_cell(0, 4, "Legend: F = Full | H = Half | A = Absent | L = Late | - = Holiday/Tuesday", align="L")
        self.ln(4)

    def add_salary_section(self, data):
        self.set_font(FONT_NAME, "B", 10)
        self.cell(0, 6, "Salary Breakdown", ln=True)
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font(FONT_NAME, "", 10)
        self.ln(4)

        items = list(data.items())
        for i in range(0, len(items), 2):
            label1, value1 = items[i]
            label2, value2 = items[i + 1] if i + 1 < len(items) else ("", "")
            self.set_font(FONT_NAME, "B" if label1 in ["Gross Pay"] else "", 10)
            self.cell(55, 6, f"{label1}:", border=0)
            self.cell(35, 6, f"{value1}", border=0, align="R")
            self.set_font(FONT_NAME, "B" if label2 in ["Gross Pay"] else "", 10)
            self.cell(55, 6, f"{label2}:", border=0)
            self.cell(0, 6, f"{value2}", ln=True, align="R")

    def add_leave_summary(self, summary):
        self.set_font(FONT_NAME, "B", 10)
        self.ln(4)
        self.cell(0, 6, "Leave Adjustment Summary", ln=True)
        self.ln(4)
        self.set_draw_color(160, 160, 160)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font(FONT_NAME, "", 10)
        self.ln(2)

        items = list(summary.items())
        for i in range(0, len(items), 2):
            label1, value1 = items[i]
            label2, value2 = items[i + 1] if i + 1 < len(items) else ("", "")
            self.set_font(FONT_NAME, "B" if label1 in ["Net Salary Payable"] else "", 10)
            self.cell(55, 6, f"{label1}:", border=0)
            self.cell(35, 6, f"{value1}", border=0, align="R")
            self.set_font(FONT_NAME, "B" if label2 in ["Net Salary Payable"] else "", 10)
            self.cell(55, 6, f"{label2}:", border=0)
            self.cell(0, 6, f"{value2}", ln=True, align="R")

    def add_notes(self, notes):
        if self.get_y() > 250:
            self.add_page()
        self.ln(4)
        self.set_font(FONT_NAME, "B", 9)
        self.cell(0, 5, "Notes:", ln=True)
        self.set_font(FONT_NAME, "I", 9)
        self.ln(4)

        rendered_any = False

        for idx, note in enumerate(notes):
            note = str(note).replace("\n", " ").replace("\r", "").strip()
            if not note:
                continue

            note = re.sub(r"([a-z])([A-Z])", r"\1 \2", note)

            words = []
            for word in note.split():
                word = str(word)
                if len(word) > 40:
                    chunks = [word[i:i + 30] + "-" for i in range(0, len(word), 30)]
                    words.extend(chunks)
                else:
                    words.append(word)
            note = " ".join(words)

            note = note.replace("₹", "Rs.")

            try:
                self.multi_cell(0, 5, note, align="L")
                rendered_any = True
            except Exception as e:
                print(f"[Note {idx + 1} ERROR] {e}")
                print("❌ Failed note content:", note)
                continue

        if rendered_any:
            self.ln(10)

    def render_footer(self, emp_id, month_str):
        self.set_y(-100)
        self.set_font(FONT_NAME, "I", 9)
        generated = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 4,
                  f"Shri Swami Samarth Pvt. Ltd. • This is a system-generated payslip • Generated on: {generated}",
                  ln=True, align="C")
        self.cell(0, 4, f"Payslip Format v1.3 • Document ID: SSPL-{emp_id}-{month_str}", ln=True, align="C")
        self.ln(4)
        self.cell(0, 4, "__________________________", ln=True, align="R")
        self.cell(0, 4, "Authorized Signature", ln=True, align="R")

def generate_payslip_pdf(name, emp_id, monthly_data):
    pdf = PayslipPDF()
    month_str = monthly_data.get("Month", "N/A")
    dt = datetime.strptime(month_str, "%B %Y")
    year, month = dt.year, dt.month
    attendance_map = monthly_data.get("attendance_map", {})
    holidays = monthly_data.get("holidays", [])

    pdf.add_title(name, emp_id, month_str)
    pdf.add_attendance_calendar(year, month, attendance_map, holidays)

    salary_block = {
        "Full Days": f"{monthly_data.get('full_days', 0)}",
        "Half Days": f"{monthly_data.get('half_days', 0)}",
        "Late Marks": f"{monthly_data.get('late_marks', 0)}",
        "Base Salary": f"Rs. {monthly_data.get('base_salary', 0):,.2f}",
        "Extra Pay": f"Rs. {monthly_data.get('extra_pay', 0):,.2f}",
        "Tuesday Bonus": f"Rs. {monthly_data.get('tuesday_bonus', 0):,.2f}",
        "Festival Bonus": f"Rs. {monthly_data.get('festival_bonus', 0):,.2f}",
        "Late Deduction": f"Rs. {monthly_data.get('late_deduction', 0):,.2f}",
        "Employee PF": f"Rs. {monthly_data.get('employee_pf', 0):,.2f}",
        "Employer PF": f"Rs. {monthly_data.get('employer_pf', 0):,.2f}",
        "Tax Deduction": f"Rs. {monthly_data.get('tax_deduction', 0):,.2f}",
        "Gross Pay": f"Rs. {monthly_data.get('gross_salary', 0):,.2f}",
    }

    leave_summary = {
        "Leave Concession Granted": f"{monthly_data.get('leave_concession', 0)} day(s)",
        "Concession Amount": f"Rs. {monthly_data.get('leave_concession_amount', 0):,.2f}",
        "Total Leave Taken": f"{monthly_data.get('lop_days', 0)} day(s)",
        "Loss of Pay (LOP)": f"Rs. {monthly_data.get('lop_deduction', 0):,.2f}",
        "Net Salary Payable": f"Rs. {monthly_data.get('net_salary', 0):,.2f}",
        "Total Employer CTC": f"Rs. {monthly_data.get('ctc_total', 0):,.2f}",
    }

    notes = [
        "Provident Fund calculated at 12% of Fixed Salary, capped at Rs. 1800/month as per EPF guidelines.",
        f"Leave concession applied. Amount: Rs. {round(monthly_data.get('leave_concession_amount', 0), 2)}",
        f"Days considered: {monthly_data.get('leave_concession', 0)}",
        f"Salary has been prorated based on {monthly_data.get('full_days', 0)} working days out of 26."
    ]

    pdf.add_salary_section(salary_block)
    pdf.add_leave_summary(leave_summary)
    pdf.add_notes(notes)
    pdf.render_footer(emp_id, month_str)

    return bytes(pdf.output(dest="S"))