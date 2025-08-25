# employee_qr_generator.py
import pandas as pd
import qrcode
import json
import random
import string
from datetime import datetime, timedelta
from PIL import Image
import streamlit as st
import io
import base64
import os

import io

def load_app_link_from_manifest(manifest_path="manifest.json", base_url=None):
    """Load app link from manifest.json and return absolute URL"""
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                start_url = manifest.get("start_url", "/")
                scope = manifest.get("scope", "/")

                # If base_url provided, build full absolute URL
                if base_url:
                    return base_url.rstrip("/") + "/" + start_url.lstrip("/")
                return start_url
        except Exception as e:
            st.warning(f"⚠️ Could not read manifest.json: {e}")
    return None


class EmployeeQRGenerator:
    def __init__(self, app_download_link=None):
        # You can pass your domain here if needed
        manifest_link = load_app_link_from_manifest("manifest.json", base_url="https://attendance.mycompany.com")
        self.app_download_link = app_download_link or manifest_link or \
            "https://play.google.com/store/apps/details?id=com.yourcompany.app"
        self.qr_credentials = {}

    def generate_username(self, employee_name):
        """Generate username based on employee name"""
        clean_name = ''.join(c for c in employee_name.lower() if c.isalpha())[:6]
        random_num = ''.join(random.choices(string.digits, k=4))
        return f"{clean_name}{random_num}"

    def generate_password(self, length=10):
        """Generate secure random password"""
        characters = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(random.choices(characters, k=length))

    def create_qr_data(self, employee_row, username, password):
        """Create structured QR code data"""
        qr_data = {
            "appLink": self.app_download_link,
            "credentials": {
                "username": username,
                "password": password,
                "oneTimeUse": True,
                "expiresIn": "24 hours",
                "generatedAt": datetime.now().isoformat()
            },
            "employee": {
                "id": str(employee_row.get('employee_id', '')),
                "name": str(employee_row.get('employee_name', '')),
                "email": str(employee_row.get('email_id', '')),
                "department": str(employee_row.get('department', '')),
                "role": str(employee_row.get('role', ''))
            },
            "companyInfo": {
                "name": "Your Company Name",
                "timestamp": datetime.now().isoformat()
            }
        }
        return json.dumps(qr_data)

    def generate_qr_code(self, employee_row):
        """Generate QR code for an employee"""
        employee_name = employee_row.get('employee_name', 'Unknown')
        employee_id = employee_row.get('employee_id', 'Unknown')

        # Generate credentials
        username = self.generate_username(employee_name)
        password = self.generate_password()

        # Store credentials for this employee
        self.qr_credentials[employee_id] = {
            'username': username,
            'password': password,
            'generated_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }

        # Create QR data
        qr_data = self.create_qr_data(employee_row, username, password)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        # Assuming qr_img is a PIL.Image.Image object
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        # Now pass the bytes to st.image
        st.image(buf, caption="Scan QR Code", width=200)

        # 🔑 Ensure it's a true PIL.Image.Image
        if hasattr(qr_img, "get_image"):  # for qrcode's PilImage wrapper
            qr_img = qr_img.get_image()

        return qr_img, username, password

    def save_qr_code(self, qr_img, employee_name, employee_id):
        """Save QR code as image file"""
        if not os.path.exists('qr_codes'):
            os.makedirs('qr_codes')

        filename = f"qr_codes/{employee_name}_{employee_id}_QR.png"
        qr_img.save(filename)
        return filename

    def get_qr_as_bytes(self, qr_img):
        """Convert QR code image to bytes for download"""
        img_bytes = io.BytesIO()
        qr_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()


# Streamlit Integration Functions
def display_employee_qr_interface():
    """Main Streamlit interface for employee QR generation"""
    st.title("🏢 Employee QR Code Generator")
    st.markdown("---")

    # Initialize QR generator
    if 'qr_generator' not in st.session_state:
        st.session_state.qr_generator = EmployeeQRGenerator()

    # App configuration
    st.sidebar.header("📱 App Configuration")
    app_link = st.sidebar.text_input(
        "Mobile App Download Link",
        value="https://play.google.com/store/apps/details?id=com.yourcompany.app",
        help="Enter your mobile app's download URL"
    )
    st.session_state.qr_generator.app_download_link = app_link

    # Load employee data
    try:
        # Adjust the path based on your project structure
        employee_df = pd.read_csv('data/employee_master.csv')
        st.success(f"✅ Loaded {len(employee_df)} employees from employee_master.csv")
    except FileNotFoundError:
        st.error("❌ employee_master.csv not found in data folder")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading employee data: {str(e)}")
        st.stop()

    # Display employee data with QR generation
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("👥 Employee Master Data")

        # Search functionality
        search_term = st.text_input("🔍 Search employees", placeholder="Search by name, department, or role")

        # Filter employees based on search
        if search_term:
            filtered_df = employee_df[
                employee_df['employee_name'].str.contains(search_term, case=False, na=False) |
                employee_df['department'].str.contains(search_term, case=False, na=False) |
                employee_df['role'].str.contains(search_term, case=False, na=False)
                ]
        else:
            filtered_df = employee_df

        # Display employee table with QR generation buttons
        for idx, row in filtered_df.iterrows():
            with st.expander(f"👤 {row['employee_name']} - {row['department']}"):
                col_info, col_action = st.columns([3, 1])

                with col_info:
                    st.write(f"**Employee ID:** {row['employee_id']}")
                    st.write(f"**Email:** {row.get('email_id', 'N/A')}")
                    st.write(f"**Department:** {row['department']}")
                    st.write(f"**Role:** {row['role']}")
                    st.write(f"**Join Date:** {row.get('join_date', 'N/A')}")

                with col_action:
                    if st.button(f"📱 Generate QR", key=f"qr_{row['employee_id']}"):
                        st.session_state.selected_employee = row.to_dict()

    with col2:
        st.header("📱 QR Code Generator")

        if 'selected_employee' in st.session_state:
            employee = st.session_state.selected_employee

            st.subheader(f"QR for {employee['employee_name']}")

            # Generate QR code
            qr_img, username, password = st.session_state.qr_generator.generate_qr_code(employee)

            # Display QR code
            st.image(qr_img, caption="Scan QR Code", width=200)

            # Display credentials
            st.info(f"""
            🔐 **Generated Credentials**

            **Employee:** {employee['employee_name']}
            **Username:** {username}
            **Password:** {password}
            **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            ⏰ *Expires in 24 hours | One-time use only*
            """)

            # Download QR code
            qr_bytes = st.session_state.qr_generator.get_qr_as_bytes(qr_img)
            st.download_button(
                label="💾 Download QR Code",
                data=qr_bytes,
                file_name=f"{employee['employee_name']}_QR.png",
                mime="image/png"
            )

            # Regenerate button
            if st.button("🔄 Regenerate Credentials"):
                st.rerun()
        else:
            st.info("Select an employee from the left to generate QR code")

    # Statistics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Employees", len(employee_df))

    with col2:
        departments = employee_df['department'].nunique()
        st.metric("Departments", departments)

    with col3:
        qr_generated = len(st.session_state.qr_generator.qr_credentials)
        st.metric("QR Codes Generated", qr_generated)


def add_employee_with_qr():
    """Function to add new employee with QR generation"""
    st.header("➕ Add New Employee")

    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)

        with col1:
            employee_name = st.text_input("Employee Name*")
            email_id = st.text_input("Email ID*")
            department = st.selectbox("Department",
                                      ["electrical", "electronic", "design", "mechanical", "software"])

        with col2:
            role = st.selectbox("Role",
                                ["team leader", "team member", "team helper", "manager", "senior"])
            fixed_salary = st.number_input("Fixed Salary", min_value=0, step=1000)
            join_date = st.date_input("Join Date")

        submitted = st.form_submit_button("Add Employee & Generate QR")

        if submitted:
            if employee_name and email_id:
                # Create new employee record
                new_employee = {
                    'employee_id': f"EMP{random.randint(100, 999)}",
                    'employee_name': employee_name,
                    'department': department,
                    'role': role,
                    'fixed_salary': fixed_salary,
                    'join_date': join_date.strftime('%d-%m-%Y'),
                    'email_id': email_id,
                    'performance_rating': 0,
                    'appraisal': 0
                }

                # Load existing data and append
                try:
                    df = pd.read_csv('data/employee_master.csv')
                    df = pd.concat([df, pd.DataFrame([new_employee])], ignore_index=True)
                    df.to_csv('data/employee_master.csv', index=False)

                    st.success(f"✅ Employee {employee_name} added successfully!")

                    # Generate QR code immediately
                    if 'qr_generator' not in st.session_state:
                        st.session_state.qr_generator = EmployeeQRGenerator()

                    qr_img, username, password = st.session_state.qr_generator.generate_qr_code(new_employee)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(qr_img, caption="QR Code for New Employee", width=200)

                    with col2:
                        st.info(f"""
                        🔐 **Generated Credentials**

                        **Username:** {username}
                        **Password:** {password}
                        **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """)

                    # Download button
                    qr_bytes = st.session_state.qr_generator.get_qr_as_bytes(qr_img)
                    st.download_button(
                        label="💾 Download QR Code",
                        data=qr_bytes,
                        file_name=f"{employee_name}_QR.png",
                        mime="image/png"
                    )

                except Exception as e:
                    st.error(f"❌ Error adding employee: {str(e)}")
            else:
                st.error("❌ Please fill in all required fields")


# Main function to integrate with your existing app
def main():
    """Main function - integrate this into your existing Streamlit app"""

    # Add QR functionality to your existing navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page",
                                ["Employee QR Generator", "Add Employee with QR", "Your Existing Pages..."])

    if page == "Employee QR Generator":
        display_employee_qr_interface()
    elif page == "Add Employee with QR":
        add_employee_with_qr()


if __name__ == "__main__":
    main()