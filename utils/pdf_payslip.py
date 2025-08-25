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
        self.set_auto_page_break(auto=False)  # Disable auto page break for single page control
        self.custom_fonts_loaded = False
        self.font_family = "Arial"  # Default fallback

        # Try to load custom fonts first
        self._load_custom_fonts()

        # Set initial font
        self.set_font(self.font_family, "", 10)
        self.add_page()

    def _load_custom_fonts(self):
        """Try to load custom DejaVu fonts with proper error handling"""
        try:
            # Check if font files exist
            regular_font = os.path.join(FONT_PATH, "DejaVuSans.ttf")
            bold_font = os.path.join(FONT_PATH, "DejaVuSans-Bold.ttf")
            italic_font = os.path.join(FONT_PATH, "DejaVuSans-Oblique.ttf")

            if all(os.path.exists(f) for f in [regular_font, bold_font, italic_font]):
                # Try to load custom fonts
                self.add_font(FONT_NAME, "", regular_font, uni=True)
                self.add_font(FONT_NAME, "B", bold_font, uni=True)
                self.add_font(FONT_NAME, "I", italic_font, uni=True)
                self.custom_fonts_loaded = True
                self.font_family = FONT_NAME
                print("Custom DejaVu fonts loaded successfully.")
            else:
                print(f"Font files not found in {FONT_PATH}. Using Arial fallback.")

        except Exception as e:
            print(f"Custom fonts not available: {e}. Using Arial fallback.")
            self.custom_fonts_loaded = False
            self.font_family = "Arial"

    def safe_set_font(self, style="", size=10):
        """Safely set font with robust fallback handling"""
        try:
            # Always use the determined font family
            self.set_font(self.font_family, style, size)
        except Exception as e:
            try:
                # If that fails, force Arial
                print(f"Font setting error with {self.font_family}: {e}. Forcing Arial.")
                self.font_family = "Arial"
                self.set_font("Arial", style, size)
            except Exception as e2:
                # Last resort - use Arial without style
                print(f"Critical font error: {e2}. Using Arial without style.")
                self.set_font("Arial", "", size)

    def header(self):
        self.safe_set_font("B", 12)  # Reduced from 14
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, "Shri Swami Samarth Pvt. Ltd.", ln=True, align="C")  # Reduced height

        self.safe_set_font("", 9)  # Reduced from 10
        self.cell(0, 5, "SALARY SLIP", ln=True, align="C")  # Reduced height

        self.set_draw_color(100, 100, 100)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(5)  # Reduced from 8

    def add_employee_header(self, name, emp_id, month_str):
        # Employee details header
        self.safe_set_font("B", 10)  # Reduced from 11
        self.cell(0, 6, f"Employee: {name} | ID: {emp_id} | Period: {month_str}", ln=True, align="C")  # Reduced height
        self.ln(3)  # Reduced from 5

    def add_attendance_calendar(self, year, month, attendance_map, holidays=None):
        if holidays is None:
            holidays = []

        self.safe_set_font("B", 9)  # Reduced from 10
        self.set_fill_color(230, 230, 255)
        self.cell(0, 6, f"Attendance Calendar - {calendar.month_name[month]} {year}", ln=True, fill=True,
                  align="C")  # Reduced height
        self.ln(1)  # Reduced from 2

        self.safe_set_font("", 8)  # Reduced from 9
        self.set_draw_color(150, 150, 150)
        self.set_line_width(0.2)

        # Week headers
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.set_fill_color(240, 240, 240)
        for day in weekdays:
            self.cell(25.7, 5, txt=day, border=1, align="C", fill=True)  # Reduced height from 6
        self.ln()

        # Calendar grid
        first_weekday, total_days = calendar.monthrange(year, month)
        current_day = 1
        row_count = 0

        while current_day <= total_days:
            # Alternate row colors
            self.set_fill_color(255, 255, 255) if row_count % 2 == 0 else self.set_fill_color(248, 248, 248)

            for weekday in range(7):
                if (current_day == 1 and weekday < first_weekday) or current_day > total_days:
                    self.cell(25.7, 5, txt="", border=1, fill=True)  # Reduced height from 6
                else:
                    dt = date(year, month, current_day)
                    marker = attendance_map.get(current_day, "")

                    # Default marker logic
                    if not marker:
                        if dt.weekday() == 1:  # Tuesday
                            marker = "-"
                        elif dt.weekday() == 6:  # Sunday
                            marker = "-"
                        elif dt.isoformat() in holidays:
                            marker = "-"
                        else:
                            marker = "A"

                    # Color coding for different attendance types
                    if marker == "F":
                        self.set_fill_color(200, 255, 200)  # Light green for full day
                    elif marker == "H":
                        self.set_fill_color(255, 255, 200)  # Light yellow for half day
                    elif marker == "L":
                        self.set_fill_color(255, 200, 200)  # Light red for late
                    elif marker == "A":
                        self.set_fill_color(255, 180, 180)  # Red for absent
                    else:
                        self.set_fill_color(220, 220, 220)  # Gray for holidays/off days

                    label = f"{current_day:02d} {marker}"
                    self.cell(25.7, 5, txt=label, border=1, align="C", fill=True)  # Reduced height from 6
                    current_day += 1

            row_count += 1
            self.ln()

        self.ln(2)  # Reduced from 3
        # Legend
        self.safe_set_font("I", 7)  # Reduced from 8
        self.set_fill_color(255, 255, 255)
        legend_text = "Legend: F=Full Day | H=Half Day | L=Late Mark | A=Absent | -=Holiday/Off Day"
        self.multi_cell(0, 3, legend_text, align="C")  # Reduced height from 4
        self.ln(4)  # Reduced from 6

    def add_salary_breakdown(self, data):
        # Earnings Section
        self.safe_set_font("B", 10)  # Reduced from 11
        self.set_fill_color(230, 255, 230)
        self.cell(90, 6, "EARNINGS", border=1, fill=True, align="C")  # Reduced height from 8

        # Deductions Section Header
        self.cell(90, 6, "DEDUCTIONS", border=1, fill=True, align="C", ln=True)  # Reduced height from 8

        self.safe_set_font("", 9)  # Reduced from 10

        # Earnings items
        earnings_items = [
            ("Basic Salary", data.get("basic_salary", 0)),
            ("DA (Dearness Allow.)", data.get("da", 0)),
            ("HRA (House Rent)", data.get("hra", 0)),
            ("Cell Allowance", data.get("cell_allowance", 0)),
            ("Petrol Allowance", data.get("petrol_allowance", 0)),
            ("Attendance Allow.", data.get("attendance_allowance", 0)),
            ("Performance Allow.", data.get("performance_allowance", 0)),
            ("OT Hours Amount", data.get("ot_hours_amount", 0)),
            ("RD Allowance", data.get("rd_allowance", 0)),
            ("LIC Allowance", data.get("lic_allowance", 0)),
            ("Arrears Allowance", data.get("arrears_allowance", 0)),
            ("Other Allowance", data.get("other_allowance", 0)),
            ("Extra Pay", data.get("extra_pay", 0)),
            ("Festival Bonus", data.get("festival_bonus", 0)),
            ("Tuesday Bonus", data.get("tuesday_bonus", 0)),
            ("Leave Concession Amt", data.get("leave_concession_amount", 0)),
        ]

        # Deductions items
        deductions_items = [
            ("Employee PF", data.get("employee_pf", 0)),
            ("Employee ESI", data.get("employee_esi", 0)),
            ("Tax Deduction", data.get("tax_deduction", 0)),
            ("MLWF Employee", data.get("mlwf_employee", 0)),
            ("Advance Deduction", data.get("advance_deduction", 0)),
            ("Loan Deduction", data.get("loan_deduction", 0)),
            ("Loan Cutting", data.get("loan_cutting", 0)),
            ("Fine Deduction", data.get("fine_deduction", 0)),
            ("Extra Deduction", data.get("extra_deduction", 0)),
            ("LOP Deduction", data.get("lop_deduction", 0)),
        ]

        # Filter out zero values for cleaner display
        earnings_items = [(label, value) for label, value in earnings_items if float(value) > 0]
        deductions_items = [(label, value) for label, value in deductions_items if float(value) > 0]

        # Make sure both lists have the same length for parallel display
        max_items = max(len(earnings_items), len(deductions_items))

        # Pad shorter list with empty entries
        while len(earnings_items) < max_items:
            earnings_items.append(("", 0))
        while len(deductions_items) < max_items:
            deductions_items.append(("", 0))

        # Display items in parallel
        for i in range(max_items):
            # Earnings column
            earn_label, earn_value = earnings_items[i]
            if earn_label:
                self.cell(60, 5, earn_label, border=1)  # Reduced height from 6
                self.cell(30, 5, f"Rs.{float(earn_value):,.2f}", border=1, align="R")  # Reduced height from 6
            else:
                self.cell(90, 5, "", border=1)  # Reduced height from 6

            # Deductions column
            ded_label, ded_value = deductions_items[i]
            if ded_label:
                self.cell(60, 5, ded_label, border=1)  # Reduced height from 6
                self.cell(30, 5, f"Rs.{float(ded_value):,.2f}", border=1, align="R", ln=True)  # Reduced height from 6
            else:
                self.cell(90, 5, "", border=1, ln=True)  # Reduced height from 6

        # Totals row
        self.safe_set_font("B", 9)  # Reduced from 10
        self.set_fill_color(240, 240, 240)

        gross_earnings = float(data.get("gross_earnings", 0))
        total_deductions = float(data.get("total_deductions", 0))

        self.cell(60, 6, "GROSS EARNINGS", border=1, fill=True)  # Reduced height from 8
        self.cell(30, 6, f"Rs.{gross_earnings:,.2f}", border=1, align="R", fill=True)  # Reduced height from 8
        self.cell(60, 6, "TOTAL DEDUCTIONS", border=1, fill=True)  # Reduced height from 8
        self.cell(30, 6, f"Rs.{total_deductions:,.2f}", border=1, align="R", fill=True,
                  ln=True)  # Reduced height from 8

        self.ln(2)  # Reduced from 4

    def add_net_salary_summary(self, data):
        self.safe_set_font("B", 11)  # Reduced from 12
        self.set_fill_color(255, 255, 200)

        net_salary = float(data.get("net_salary", 0))
        ctc = float(data.get("ctc", 0))
        fixed_salary = float(data.get("fixed_salary", 0))

        # Net salary box
        self.cell(0, 8, f"NET SALARY PAYABLE: Rs.{net_salary:,.2f}", border=1, fill=True, align="C",
                  ln=True)  # Reduced height from 10

        self.ln(1)  # Reduced from 2

        # Additional summary info
        self.safe_set_font("", 9)  # Reduced from 10
        self.cell(60, 5, f"Fixed Salary: Rs.{fixed_salary:,.2f}")  # Reduced height from 6
        self.cell(60, 5, f"CTC: Rs.{ctc:,.2f}", align="R", ln=True)  # Reduced height from 6

        self.ln(3)  # Reduced from 4

    def add_attendance_summary(self, data):
        self.safe_set_font("B", 9)  # Reduced from 10
        self.set_fill_color(230, 230, 255)
        self.cell(0, 6, "ATTENDANCE & LEAVE SUMMARY", border=1, fill=True, align="C", ln=True)  # Reduced height from 8

        self.safe_set_font("", 8)  # Reduced from 9

        # Attendance details
        attendance_data = [
            ("Full Days", int(data.get("full_days", 0))),
            ("Half Days", int(data.get("half_days", 0))),
            ("Late Marks", int(data.get("late_marks", 0))),
            ("LOP Days", int(data.get("lop_days", 0))),
            ("Days in Month", int(data.get("days_in_month", 0))),
            ("Working Days", int(data.get("working_days", 0))),
            ("Leave Concession", float(data.get("leave_concession", 0))),
            ("Tuesday Count", int(data.get("tuesday_count", 0))),
        ]

        # Display in 2 columns
        for i in range(0, len(attendance_data), 2):
            label1, value1 = attendance_data[i]
            self.cell(60, 5, f"{label1}:", border=1)  # Reduced height from 6
            self.cell(30, 5, str(value1), border=1, align="C")  # Reduced height from 6

            if i + 1 < len(attendance_data):
                label2, value2 = attendance_data[i + 1]
                self.cell(60, 5, f"{label2}:", border=1)  # Reduced height from 6
                self.cell(30, 5, str(value2), border=1, align="C")  # Reduced height from 6

            self.ln()

        self.ln(2)  # Reduced from 4

    def add_statutory_info(self, data):
        self.safe_set_font("B", 9)  # Reduced from 10
        self.set_fill_color(255, 240, 240)
        self.cell(0, 6, "STATUTORY CONTRIBUTIONS", border=1, fill=True, align="C", ln=True)  # Reduced height from 8

        self.safe_set_font("", 8)  # Reduced from 9

        # Statutory details - Only show non-zero values to save space
        all_statutory_data = [
            ("Employee PF", float(data.get('employee_pf', 0))),
            ("Employer PF", float(data.get('employer_pf', 0))),
            ("Employee ESI", float(data.get('employee_esi', 0))),
            ("Employer ESI", float(data.get('employer_esi', 0))),
            ("PF Admin Charges", float(data.get('pf_admin_charges', 0))),
            ("MLWF Employee", float(data.get('mlwf_employee', 0))),
            ("MLWF Employer", float(data.get('mlwf_employer', 0))),
        ]

        # Filter out zero values
        statutory_data = [(label, f"Rs.{value:,.2f}") for label, value in all_statutory_data if value > 0]

        # If odd number of items, add empty entry
        if len(statutory_data) % 2 == 1:
            statutory_data.append(("", ""))

        # Display in 2 columns
        for i in range(0, len(statutory_data), 2):
            label1, value1 = statutory_data[i]
            if label1:
                self.cell(60, 5, f"{label1}:", border=1)  # Reduced height from 6
                self.cell(30, 5, value1, border=1, align="R")  # Reduced height from 6
            else:
                self.cell(90, 5, "", border=1)  # Reduced height from 6

            if i + 1 < len(statutory_data):
                label2, value2 = statutory_data[i + 1]
                if label2:
                    self.cell(60, 5, f"{label2}:", border=1)  # Reduced height from 6
                    self.cell(30, 5, value2, border=1, align="R")  # Reduced height from 6
                else:
                    self.cell(90, 5, "", border=1)  # Reduced height from 6

            self.ln()

        self.ln(2)  # Reduced from 4

    def add_notes_and_disclaimers(self, data):
        # Check available space and limit notes accordingly
        available_space = 297 - self.get_y() - 30  # A4 height minus current position minus footer space

        self.safe_set_font("B", 8)  # Reduced from 9
        self.cell(0, 4, "NOTES & DISCLAIMERS:", ln=True)  # Reduced height from 6
        self.ln(1)  # Reduced from 2

        self.safe_set_font("", 7)  # Reduced from 8

        notes = []

        # Dynamic notes based on data - keep only essential ones
        if float(data.get("employee_pf", 0)) > 0:
            basic_salary = max(float(data.get("basic_salary", 1)), 1)  # Avoid division by zero
            pf_rate = min(12, (float(data.get("employee_pf", 0)) / basic_salary) * 100)
            notes.append(f"• Provident Fund deducted at {pf_rate:.1f}% of Basic Salary as per EPF regulations.")

        if float(data.get("lop_deduction", 0)) > 0:
            notes.append(
                f"• Loss of Pay deduction: Rs.{float(data.get('lop_deduction', 0)):,.2f} for {int(data.get('lop_days', 0))} day(s).")

        # Only add if space allows
        if available_space > 20:
            notes.append("• This is a computer-generated payslip and does not require a physical signature.")

        # Render only first few notes if space is limited
        max_notes = 3 if available_space < 30 else len(notes)
        for i, note in enumerate(notes[:max_notes]):
            try:
                # Clean up the note text
                clean_note = str(note).strip()
                if clean_note:
                    self.multi_cell(0, 4, clean_note, align="L")  # Reduced height from 5
            except Exception as e:
                print(f"Error rendering note: {e}")
                continue

        self.ln(3)  # Reduced from 8

    def add_footer(self, emp_id, month_str):
        # Calculate position to place footer at bottom without overflow
        footer_height = 20
        max_y = 297 - footer_height  # A4 height minus footer space

        if self.get_y() > max_y:
            self.set_y(max_y)
        else:
            # Move to bottom area
            self.set_y(-25)  # Reduced from -40

        # Signature line
        self.safe_set_font("", 8)  # Reduced from 9
        self.cell(0, 4, "_" * 30, ln=True, align="R")  # Reduced height from 6
        self.cell(0, 4, "Authorized Signatory", ln=True, align="R")  # Reduced height from 6

        self.ln(2)  # Reduced from 4

        # Company footer
        self.safe_set_font("I", 7)  # Reduced from 8
        generated_on = datetime.now().strftime("%d-%m-%Y %H:%M")
        footer_text = f"Shri Swami Samarth Pvt. Ltd. | Generated: {generated_on} | Doc ID: SSPL-{emp_id}-{month_str.replace(' ', '-')}"
        self.cell(0, 3, footer_text, ln=True, align="C")  # Reduced height from 4


def generate_payslip_pdf(name, emp_id, monthly_data):
    """
    Generate a comprehensive PDF payslip that fits on a single page
    """
    try:
        pdf = PayslipPDF()

        # Extract month information
        month_str = monthly_data.get("Month", "N/A")

        try:
            dt = datetime.strptime(month_str, "%B %Y")
            year, month = dt.year, dt.month
        except ValueError:
            # Fallback if date parsing fails
            year, month = datetime.now().year, datetime.now().month

        # Get attendance data
        attendance_map = monthly_data.get("attendance_map", {})
        holidays = monthly_data.get("holidays", [])

        # Generate PDF sections with optimized spacing
        pdf.add_employee_header(name, emp_id, month_str)
        pdf.add_attendance_calendar(year, month, attendance_map, holidays)
        pdf.add_salary_breakdown(monthly_data)
        pdf.add_net_salary_summary(monthly_data)
        pdf.add_attendance_summary(monthly_data)
        pdf.add_statutory_info(monthly_data)
        pdf.add_notes_and_disclaimers(monthly_data)
        pdf.add_footer(emp_id, month_str)

        # Return PDF as bytes
        return bytes(pdf.output(dest="S"))

    except Exception as e:
        print(f"Error generating PDF: {e}")
        # Return a minimal error PDF with proper font handling
        try:
            error_pdf = FPDF()
            error_pdf.add_page()
            error_pdf.set_font("Arial", "", 12)
            error_pdf.cell(0, 10, f"Error generating payslip for {name} ({emp_id})", ln=True)
            error_pdf.cell(0, 10, f"Error details: {str(e)}", ln=True)
            error_pdf.cell(0, 10, "Please contact system administrator.", ln=True)
            return bytes(error_pdf.output(dest="S"))
        except Exception as e2:
            print(f"Critical error even generating error PDF: {e2}")
            # Return empty bytes if everything fails
            return b""