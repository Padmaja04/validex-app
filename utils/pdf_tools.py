from fpdf import FPDF
from datetime import datetime

def generate_pdf_summary(company_name, top_employee_name, top_score, summary_df, log_df,
                         leave_summary=None, selected_month=None):
    month_str = selected_month if selected_month else datetime.today().strftime("%B %Y")
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf", uni=True)

    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, f"{company_name}", ln=True, align="C")
    pdf.cell(0, 10, f"– Payroll Highlights – {month_str}", ln=True, align="C")
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 8, f"🏆 Employee of the Month: {top_employee_name.title()} – Score: {top_score:.2f}", ln=True)
    pdf.cell(0, 8, "———", ln=True)
    pdf.cell(0, 8, "✨ Featured Employees:", ln=True)
    for _, row in summary_df.iterrows():
        badge_clean = "🏅 " + row["badges"].replace(">", "").strip()
        pdf.cell(0, 8, f"• {row['employee_name'].title()} – {badge_clean}", ln=True)

    pdf.cell(0, 8, "———", ln=True)
    pdf.cell(0, 8, "📊 Payroll Summary:", ln=True)
    pdf.cell(0, 8, f"• Total YTD Salary: ₹{log_df['net_salary'].sum():,.2f}", ln=True)
    pdf.cell(0, 8, f"• Badges Awarded: {summary_df.shape[0]}", ln=True)
    pdf.cell(0, 8, f"• Employees Processed: {log_df['employee_id'].nunique()}", ln=True)

    pdf.cell(0, 8, "———", ln=True)
    pdf.cell(0, 8, "📄 Recent Payroll Entries:", ln=True)
    recent = log_df[["employee_name", "month_str", "net_salary", "badges"]].tail(5)
    for _, row in recent.iterrows():
        badge = "🏅 " + str(row["badges"]).replace(">", "").strip()
        pdf.cell(0, 8, f"- {row['employee_name'].title()} | {row['month_str']} | ₹{row['net_salary']:,.2f} | {badge}", ln=True)

    # 🗓️ Leave Summary
    if leave_summary is not None and not leave_summary.empty:
        pdf.cell(0, 8, "———", ln=True)
        pdf.cell(0, 8, "🗓️ Leave Balance Overview:", ln=True)
        for _, row in leave_summary.iterrows():
            pdf.cell(0, 8, f"- {row['employee_name'].title()}: {row['leave_balance']:.2f} days", ln=True)
        avg_leave = leave_summary["leave_balance"].mean()
        pdf.cell(0, 8, f"• Average Leave Balance: {avg_leave:.1f} days", ln=True)

    import io
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer