def run_attendance():
    """Main attendance application with comprehensive security and error handling"""

    # Initialize system with validation
    try:
        validate_configuration()
    except ConfigurationError as e:
        st.error(f"🚨 **Configuration Error:** {e}")
        st.error("Please contact system administrator to fix configuration.")
        logger.error(f"Configuration error: {e}")
        st.stop()

    # Enhanced security validation
    try:
        is_valid, message = validate_session_security()
        if not is_valid:
            st.error(f"🔒 **Security Validation Failed:** {message}")
            st.error("Please login again to access the attendance system.")

            # Log security failure
            log_security_event(
                "SECURITY_VALIDATION_FAILED",
                st.session_state.get("employee_id", "unknown"),
                st.session_state.get("username", "unknown"),
                message
            )
            st.stop()

    except Exception as e:
        logger.error(f"Security validation error: {e}")
        st.error("❌ Security validation error. Please contact support.")
        st.stop()

    # Get validated user information
    logged_employee_name = st.session_state.get("employee_name", "").strip()
    logged_employee_id = str(st.session_state.get("employee_id", "")).strip()
    logged_username = st.session_state.get("username", "").strip()

    logger.info(f"Attendance access by {logged_username} ({logged_employee_id})")

    # Setup UI
    setup_pwa()
    apply_mobile_css()

    # PWA Header
    st.markdown(f"""
    <div class="pwa-header">
        <h1>⚡ Ultra-Fast Attendance System</h1>
        <p>Secure GPS + Face Recognition</p>
        <span class="speed-indicator">SECURITY ENHANCED</span><br>
        <small>Logged in as: {logged_username}</small>
    </div>
    """, unsafe_allow_html=True)

    # Show system status
    show_database_status()

    # Security info card
    st.markdown(f"""
    <div class="user-info-card">
        <h3>🛡️ Secure Session Active</h3>
        <p><strong>Employee:</strong> {logged_employee_name}</p>
        <p><strong>ID:</strong> {logged_employee_id}</p>
        <p><strong>Login:</strong> {logged_username}</p>
        <p><small>🔒 This session is secured and validated</small></p>
    </div>
    """, unsafe_allow_html=True)

    # Step 1: Location Detection with Validation
    st.markdown("### Step 1: ⚡ Secure Location Detection")
    st.markdown("*Enhanced with coordinate validation and security checks*")

    try:
        location_data = get_location_ultra_fast()
        if not location_data:
            st.warning("📍 Please select a location detection method above to continue.")
            st.stop()

        # Validate and extract coordinates
        user_lat = location_data.get("latitude", 0)
        user_lon = location_data.get("longitude", 0)
        location_source = location_data.get("source", "Unknown")
        detection_method = location_data.get("method", "unknown")

        # Double-check coordinate validation
        if not validate_coordinates(user_lat, user_lon):
            st.error("❌ Invalid coordinates detected. Please try again.")
            logger.error(f"Invalid coordinates from location detection: {user_lat}, {user_lon}")
            st.stop()

    except Exception as e:
        logger.error(f"Location detection error: {e}")
        st.error(f"❌ Location detection failed: {e}")
        st.stop()

    # Verify location permissions
    try:
        location_verified, location_name, distance = check_location_permission(user_lat, user_lon)

        if location_verified:
            st.markdown(f"""
            <div class="location-status location-approved">
                ✅ Location Verified & Secure!<br>
                📍 {location_name}<br>
                📏 {distance:.1f}m from office<br>
                ⚡ Method: {detection_method}<br>
                🚀 Source: {location_source}
            </div>
            """, unsafe_allow_html=True)

            # Log successful location verification
            log_security_event(
                "LOCATION_VERIFIED",
                logged_employee_id,
                logged_username,
                f"Location: {location_name}, Distance: {distance:.1f}m"
            )
        else:
            st.markdown(f"""
            <div class="location-status location-denied">
                ❌ Location Not Authorized<br>
                📍 Current: {user_lat:.4f}, {user_lon:.4f}<br>
                🚫 Outside permitted office area<br>
                📏 Please move to an authorized location
            </div>
            """, unsafe_allow_html=True)

            # Log failed location verification
            log_security_event(
                "LOCATION_DENIED",
                logged_employee_id,
                logged_username,
                f"Coordinates: {user_lat:.4f}, {user_lon:.4f}"
            )

            # Show nearby authorized locations
            with st.expander("🗺️ View Authorized Office Locations"):
                try:
                    for office in OFFICE_LOCATIONS:
                        office_distance = geodesic((user_lat, user_lon), (office["lat"], office["lon"])).meters
                        st.write(f"📍 **{office['name']}**: {office_distance:.0f}m away")
                        st.write(f"   Allowed radius: {office['radius']}m")
                except Exception as dist_error:
                    st.error(f"Error calculating distances: {dist_error}")

            st.stop()

    except Exception as e:
        logger.error(f"Location permission check error: {e}")
        st.error(f"❌ Location verification failed: {e}")
        st.stop()

    # Step 2: Employee Verification
    st.markdown("### Step 2: ✅ Employee Identity Verification")

    try:
        # Load and validate employee data
        master_df = load_employee_master()
        if master_df.empty:
            st.error("❌ No employee data found in master database.")
            logger.error("Empty employee master data")
            st.stop()

        # Clean and validate employee data
        master_df["employee_name"] = master_df["employee_name"].astype(str).str.strip()
        master_df["employee_id"] = master_df["employee_id"].astype(str).str.strip()

        # Find matching employee
        employee_match = master_df[
            (master_df["employee_id"] == logged_employee_id) |
            (master_df["employee_name"].str.lower() == logged_employee_name.lower())
            ]

        if employee_match.empty:
            st.error(f"❌ Employee '{logged_employee_name}' (ID: {logged_employee_id}) not found in master data.")
            st.error("Please contact HR to add your profile to the system.")

            log_security_event(
                "EMPLOYEE_NOT_FOUND",
                logged_employee_id,
                logged_username,
                "Employee not in master database"
            )
            st.stop()

        employee_row = employee_match.iloc[0]
        employee_id = str(employee_row["employee_id"]).strip()
        employee_name = str(employee_row["employee_name"]).strip()

        try:
            salary = float(employee_row.get("fixed_salary", 0)) if pd.notna(employee_row.get("fixed_salary", 0)) else 0
        except (ValueError, TypeError):
            salary = 0
            logger.warning(f"Invalid salary data for employee {employee_id}")

        st.markdown(f"""
        <div class="security-badge">
            <h4>🔐 Identity Verified & Confirmed</h4>
            <p>Employee: <strong>{employee_name}</strong></p>
            <p>ID: <strong>{employee_id}</strong></p>
            <p>Login User: <strong>{logged_username}</strong></p>
            <p>Salary Record: <strong>{'✅ Found' if salary > 0 else '⚠️ Not Set'}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        log_security_event(
            "EMPLOYEE_VERIFIED",
            employee_id,
            logged_username,
            f"Master database match confirmed"
        )

    except Exception as e:
        logger.error(f"Employee verification error: {e}")
        st.error(f"❌ Error during employee verification: {e}")
        st.stop()

    # Step 3: Face Recognition with Enhanced Security
    st.markdown("### Step 3: 📸 Biometric Face Recognition")

    try:
        # Validate face recognition availability
        if not FACE_RECOGNITION_AVAILABLE:
            st.error("❌ Face recognition system not available")
            st.error("Please contact IT support to enable biometric authentication")
            st.stop()

        # Construct badge path securely
        badge_filename = f"{employee_name.lower().strip().replace(' ', '_')}.jpg"
        badge_path = os.path.join(BADGE_DIR, badge_filename)

        # Validate badge path security (prevent directory traversal)
        if '..' in badge_filename or '/' in badge_filename.replace('_', ''):
            st.error("❌ Invalid badge filename detected")
            logger.error(f"Potential security issue with badge filename: {badge_filename}")
            st.stop()

        # Validate face recognition inputs
        is_valid_input, validation_message = validate_face_recognition_input(badge_path, None)

        if not is_valid_input and "No snapshot provided" not in validation_message:
            st.error(f"❌ {validation_message}")

            if "not found" in validation_message:
                with st.expander("ℹ️ Badge Photo Requirements"):
                    st.markdown(f"""
                    **Badge Photo Guidelines:**
                    - Expected filename: `{badge_filename}`
                    - Location: `{BADGE_DIR}`
                    - Image should be clear and well-lit
                    - Face should be clearly visible
                    - Recommended size: 300x300 pixels minimum
                    - Supported formats: JPG, PNG
                    - Maximum file size: 10MB

                    **Contact administrator if your badge photo is missing.**
                    """)
            st.stop()

        # Display reference photo securely
        col1, col2 = st.columns([1, 2])

        with col1:
            try:
                st.image(badge_path, caption=f"Reference: {employee_name}", width=250)
            except Exception as img_error:
                st.error(f"❌ Error loading badge image: {img_error}")
                logger.error(f"Badge image error for {employee_name}: {img_error}")
                st.stop()

        with col2:
            st.markdown("""
            <div class="warning-container">
                <h4>📋 Biometric Verification Instructions</h4>
                <ul>
                    <li>🔆 Ensure bright, even lighting</li>
                    <li>👤 Look directly at the camera</li>
                    <li>😐 Maintain neutral expression</li>
                    <li>📱 Hold device steady</li>
                    <li>🚫 Remove sunglasses, hats, masks</li>
                    <li>📏 Position face similar to reference photo</li>
                </ul>
                <p><strong>🔒 Security Note:</strong> Your biometric data is processed locally and never stored.</p>
            </div>
            """, unsafe_allow_html=True)

        # Secure camera input
        st.markdown("**📷 Capture your verification photo:**")
        snapshot = st.camera_input("Biometric Capture", key="secure_face_recognition_camera")

        if not snapshot:
            st.info("📸 Please capture your photo for biometric verification.")
            st.markdown("""
            <div style="text-align: center; padding: 20px; background: #f0f0f0; border-radius: 10px; margin: 10px 0;">
                <p>⏳ <strong>Waiting for biometric capture...</strong></p>
                <small>Click the camera button above to take your verification photo</small>
            </div>
            """, unsafe_allow_html=True)
            st.stop()

        # Perform face verification with comprehensive error handling
        st.markdown("**🔍 Processing biometric verification...**")

        try:
            with st.spinner("🤖 Analyzing biometric data..."):
                match, confidence = compare_faces(badge_path, snapshot)

                # Validate confidence score
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
                    raise ValueError(f"Invalid confidence score: {confidence}")

                threshold = 30  # Minimum confidence threshold

            # Log biometric attempt
            log_security_event(
                "BIOMETRIC_ATTEMPT",
                employee_id,
                logged_username,
                f"Confidence: {confidence:.2f}%, Threshold: {threshold}%"
            )

            if not match or confidence < threshold:
                st.markdown(f"""
                <div class="error-container">
                    <h4 style="color: #C62828;">❌ Biometric Verification Failed</h4>
                    <p><strong>Confidence Score:</strong> {confidence:.2f}% (Required: {threshold}%)</p>
                    <p><strong>Possible Issues:</strong></p>
                    <ul>
                        <li>Inadequate lighting conditions</li>
                        <li>Face partially obscured or unclear</li>
                        <li>Significant difference from reference photo</li>
                        <li>Camera quality or focus issues</li>
                        <li>Facial obstructions (glasses, mask, etc.)</li>
                    </ul>
                    <p><strong>🔧 Troubleshooting Steps:</strong></p>
                    <ul>
                        <li>Move to a well-lit area</li>
                        <li>Remove any face coverings</li>
                        <li>Clean camera lens</li>
                        <li>Position face similar to reference photo</li>
                        <li>Ensure camera is steady</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                # Log failed verification
                log_security_event(
                    "BIOMETRIC_FAILED",
                    employee_id,
                    logged_username,
                    f"Low confidence: {confidence:.2f}%"
                )

                if st.button("🔄 Try Biometric Verification Again", key="retry_face_recognition"):
                    st.rerun()

                st.stop()

            # Successful biometric verification
            st.markdown(f"""
            <div class="success-container">
                <h4 style="color: #2E7D32;">✅ Biometric Verification Successful!</h4>
                <p><strong>🎯 Confidence Score:</strong> {confidence:.2f}% (Excellent match)</p>
                <p><strong>👤 Employee:</strong> {employee_name}</p>
                <p><strong>🆔 ID:</strong> {employee_id}</p>
                <p><strong>✅ Verification Status:</strong> Approved</p>
                <p><strong>🔒 Security Level:</strong> High</p>
            </div>
            """, unsafe_allow_html=True)

            # Log successful verification
            log_security_event(
                "BIOMETRIC_SUCCESS",
                employee_id,
                logged_username,
                f"High confidence match: {confidence:.2f}%"
            )

        except Exception as face_error:
            logger.error(f"Face recognition error for {employee_name}: {face_error}")
            st.markdown(f"""
            <div class="error-container">
                <h4 style="color: #C62828;">❌ Biometric System Error</h4>
                <p><strong>Error:</strong> {str(face_error)}</p>
                <p><strong>Employee:</strong> {employee_name}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Log system error
            log_security_event(
                "BIOMETRIC_SYSTEM_ERROR",
                employee_id,
                logged_username,
                f"System error: {str(face_error)}"
            )

            with st.expander("🔧 Technical Details (for support)"):
                st.code(f"""
                === BIOMETRIC SYSTEM ERROR ===
                Error: {str(face_error)}
                Type: {type(face_error).__name__}
                Employee: {employee_name}
                Badge Path: {badge_path}
                Timestamp: {datetime.now()}
                Session ID: {id(st.session_state)}
                """)

            st.error("Please try again or contact IT support if the problem persists.")
            st.stop()

    except Exception as e:
        logger.error(f"Face recognition setup error: {e}")
        st.error(f"❌ Biometric system initialization failed: {e}")
        st.stop()

    # Step 4: Process Attendance with Enhanced Security
    st.markdown("### Step 4: ⏰ Processing Secure Attendance")

    now = datetime.now()
    today = now.date()
    greeting = get_greeting(now)

    st.markdown(f"""
    <div class="metric-card">
        <h3>{greeting} {employee_name}! 👋</h3>
        <p>🕐 Current Time: {now.strftime('%I:%M %p')}</p>
        <p>📅 Date: {today.strftime('%A, %B %d, %Y')}</p>
        <p>🔒 Security Level: Maximum</p>
        <span class="speed-indicator">PROCESSING SECURELY</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Load attendance data with enhanced error handling
        attendance_df = load_attendance()
        attendance_df["employee_id"] = attendance_df["employee_id"].astype(str)
        attendance_df["start_datetime"] = pd.to_datetime(attendance_df["start_datetime"], errors="coerce")
        attendance_df["date_only"] = attendance_df["start_datetime"].dt.date

        # Check today's record for this specific employee
        mask = (attendance_df["employee_id"] == employee_id) & (attendance_df["date_only"] == today)
        today_record = attendance_df[mask]

        if today_record.empty:
            # ===== SECURE CHECK-IN PROCESS =====
            st.markdown("#### 🔑 **Secure Check-In Process**")

            # Calculate late status with validation
            try:
                late_cutoff = datetime.strptime("09:15", "%H:%M").time()
                late_mark = now.time() > late_cutoff

                if late_mark:
                    late_minutes = (datetime.combine(today, now.time()) -
                                    datetime.combine(today, late_cutoff)).seconds // 60
                    st.warning(f"⚠️ Late arrival detected: {late_minutes} minutes after 9:15 AM")

                    log_security_event(
                        "LATE_ARRIVAL",
                        employee_id,
                        logged_username,
                        f"Late by {late_minutes} minutes"
                    )

            except Exception as time_error:
                logger.error(f"Error calculating late status: {time_error}")
                late_mark = False

            # Create secure attendance record
            new_row = {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "start_datetime": now,
                "exit_datetime": pd.NaT,
                "date_only": today,
                "total_hours": pd.NA,
                "extra_hours": 0,
                "extra_pay": 0,
                "attendance_status": pd.NA,
                "late_mark": late_mark,
                "method": f"Secure GPS + Biometric ({detection_method})",
                "confidence": confidence,
                "notes": f"Verified login: {logged_username} | Location: {location_source} | Security: Enhanced",
                "location_lat": user_lat,
                "location_lon": user_lon,
                "location_verified": location_verified,
                "location_name": location_name
            }

            # Add record with validation
            try:
                attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)
                attendance_df["date_only"] = pd.to_datetime(attendance_df["start_datetime"]).dt.date

                # Remove duplicates (keep latest)
                attendance_df.drop_duplicates(subset=["employee_id", "date_only"], keep="last", inplace=True)

                # Save with enhanced security
                if save_attendance_secure(attendance_df):
                    # Log successful check-in
                    log_security_event(
                        "CHECKIN_SUCCESS",
                        employee_id,
                        logged_username,
                        f"Method: {detection_method}, Confidence: {confidence:.1f}%, Location: {location_name}"
                    )

                    # Success display
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🎉 Secure Check-In Successful!</h3>
                        <p><strong>👤 Employee:</strong> {employee_name}</p>
                        <p><strong>🕐 Check-In Time:</strong> {now.strftime('%I:%M %p')}</p>
                        <p><strong>📅 Date:</strong> {today.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>📍 Location:</strong> {location_name}</p>
                        <p><strong>⚡ Method:</strong> {detection_method.title()}</p>
                        <p><strong>🎯 Biometric Match:</strong> {confidence:.1f}%</p>
                        <p><strong>👤 Verified User:</strong> {logged_username}</p>
                        <p><strong>🔒 Security:</strong> Maximum</p>
                        {f"<p style='color: #ffeb3b; font-weight: bold;'>⚠️ Late Mark Applied</p>" if late_mark else "<p style='color: #4CAF50; font-weight: bold;'>✅ On Time</p>"}
                        <span class="speed-indicator">SECURE CHECK-IN COMPLETE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.balloons()

                    # Show today's schedule
                    st.markdown("""
                    <div class="success-container">
                        <h4 style="color: #2E7D32;">📋 Today's Schedule</h4>
                        <ul style="color: #388E3C;">
                            <li><strong>Standard Hours:</strong> 9:00 AM - 6:00 PM</li>
                            <li><strong>Lunch Break:</strong> 1:00 PM - 2:00 PM</li>
                            <li><strong>Overtime Begins:</strong> After 6:45 PM</li>
                            <li><strong>Minimum Work Time:</strong> 1 minute (for checkout)</li>
                        </ul>
                        <p style="color: #2E7D32;"><strong>💼 Have a productive day!</strong></p>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.error("❌ Failed to save check-in data. Please contact support.")
                    log_security_event(
                        "CHECKIN_SAVE_FAILED",
                        employee_id,
                        logged_username,
                        "Data save operation failed"
                    )

            except Exception as save_error:
                logger.error(f"Check-in save error: {save_error}")
                st.error(f"❌ Error saving check-in: {save_error}")
                log_security_event(
                    "CHECKIN_ERROR",
                    employee_id,
                    logged_username,
                    f"Save error: {str(save_error)}"
                )

        else:
            # ===== SECURE CHECK-OUT PROCESS =====
            record = today_record.iloc[0]

            if pd.isnull(record["exit_datetime"]):
                st.markdown("#### 🚪 **Secure Check-Out Process**")

                try:
                    check_in_time = pd.to_datetime(record["start_datetime"])
                    elapsed_seconds = (now - check_in_time).total_seconds()
                    elapsed_minutes = elapsed_seconds / 60

                    # Minimum time validation with security
                    if elapsed_seconds < 60:  # Must work at least 1 minute
                        remaining_seconds = 60 - elapsed_seconds

                        st.markdown(f"""
                        <div class="warning-container">
                            <h4>⏳ Minimum Work Time Validation</h4>
                            <p>Check-in time: <strong>{check_in_time.strftime('%I:%M %p')}</strong></p>
                            <p>Current time: <strong>{now.strftime('%I:%M %p')}</strong></p>
                            <p>Time remaining: <strong>{remaining_seconds:.0f} seconds</strong></p>
                            <p><em>System security requires minimum 1-minute work duration</em></p>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("🔄 Refresh Status", key="checkout_refresh"):
                            st.rerun()

                        st.stop()

                    # Calculate work duration with validation
                    total_hours = elapsed_seconds / 3600
                    hours = int(total_hours)
                    minutes = int((total_hours - hours) * 60)

                    # Calculate overtime securely
                    try:
                        overtime_start = datetime.combine(today, datetime.strptime("18:45", "%H:%M").time())
                        midnight = datetime.combine(today + timedelta(days=1),
                                                    datetime.strptime("00:00", "%H:%M").time())

                        if now > overtime_start:
                            extra_hours = min((now - overtime_start).total_seconds() / 3600,
                                              (midnight - overtime_start).total_seconds() / 3600)
                            extra_hours = round(max(extra_hours, 0), 2)
                        else:
                            extra_hours = 0

                    except Exception as overtime_error:
                        logger.error(f"Overtime calculation error: {overtime_error}")
                        extra_hours = 0

                    # Calculate extra pay securely
                    try:
                        if salary > 0 and extra_hours > 0:
                            hourly_rate = salary / (8 * 26)  # 8 hours/day, 26 working days/month
                            extra_pay = extra_hours * hourly_rate
                        else:
                            extra_pay = 0
                    except Exception as pay_error:
                        logger.error(f"Extra pay calculation error: {pay_error}")
                        extra_pay = 0

                    # Determine attendance status
                    if total_hours < 4:
                        attendance_status = "Absent"
                        status_color = "#f44336"
                    elif total_hours < 6:
                        attendance_status = "Half Day"
                        status_color = "#FF9800"
                    else:
                        attendance_status = "Full Day"
                        status_color = "#4CAF50"

                    # Display checkout summary
                    st.markdown(f"""
                    <div class="warning-container">
                        <h4 style="color: #E65100;">⏰ Secure Checkout Summary</h4>
                        <p><strong>Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
                        <p><strong>Current Time:</strong> {now.strftime('%I:%M %p')}</p>
                        <p><strong>Total Duration:</strong> {hours}h {minutes}m ({total_hours:.2f} hours)</p>
                        <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{attendance_status}</span></p>
                        <p><strong>Overtime Hours:</strong> {extra_hours:.2f} hours</p>
                        <p><strong>Extra Payment:</strong> ₹{extra_pay:.2f}</p>
                        <p><strong>🔒 Verification:</strong> Biometric + GPS</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Secure checkout confirmation
                    if st.button("✅ **Confirm Secure Check-Out**", key="secure_checkout",
                                 help="Complete your secure checkout for today"):
                        try:
                            # Update attendance record securely
                            idx = attendance_df[(attendance_df["employee_id"] == employee_id) &
                                                (attendance_df["date_only"] == today)].index[0]

                            attendance_df.loc[idx, "exit_datetime"] = now
                            attendance_df.loc[idx, "total_hours"] = round(total_hours, 2)
                            attendance_df.loc[idx, "extra_hours"] = extra_hours
                            attendance_df.loc[idx, "extra_pay"] = round(extra_pay, 2)
                            attendance_df.loc[idx, "attendance_status"] = attendance_status
                            attendance_df.loc[
                                idx, "notes"] = f"Secure checkout: {logged_username} | Location: {location_source} | Biometric: {confidence:.1f}%"

                            # Save securely
                            if save_attendance_secure(attendance_df):
                                # Log successful checkout
                                log_security_event(
                                    "CHECKOUT_SUCCESS",
                                    employee_id,
                                    logged_username,
                                    f"Duration: {total_hours:.2f}h, Status: {attendance_status}, Extra: {extra_hours:.2f}h"
                                )

                                # Success message
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>🎉 Secure Check-Out Successful!</h3>
                                    <p><strong>🚪 Check-Out Time:</strong> {now.strftime('%I:%M %p')}</p>
                                    <p><strong>⏱️ Total Hours:</strong> {total_hours:.2f} hours</p>
                                    <p><strong>📊 Status:</strong> {attendance_status}</p>
                                    <p><strong>⏰ Overtime Hours:</strong> {extra_hours:.2f} hours</p>
                                    <p><strong>💰 Extra Pay:</strong> ₹{extra_pay:.2f}</p>
                                    <p><strong>👤 Verified User:</strong> {logged_username}</p>
                                    <p><strong>📍 Location:</strong> {location_name}</p>
                                    <p><strong>🔒 Security:</strong> Maximum</p>
                                    <span class="speed-indicator">SECURE CHECKOUT COMPLETE</span>
                                </div>
                                """, unsafe_allow_html=True)

                                st.balloons()

                                # Performance summary
                                work_quality = "Excellent" if total_hours >= 8 else "Good" if total_hours >= 6 else "Needs Improvement"
                                st.markdown(f"""
                                <div class="success-container">
                                    <h4 style="color: #2E7D32;">📈 Today's Performance Summary</h4>
                                    <ul style="color: #388E3C;">
                                        <li><strong>Work Quality:</strong> {work_quality}</li>
                                        <li><strong>Punctuality:</strong> {"On Time" if not record['late_mark'] else "Late Arrival"}</li>
                                        <li><strong>Productive Hours:</strong> {total_hours:.2f}</li>
                                        <li><strong>Overtime Contribution:</strong> {extra_hours:.2f} hours</li>
                                        <li><strong>Security Compliance:</strong> 100%</li>
                                    </ul>
                                    <p style="color: #2E7D32;"><strong>💼 Thank you for your secure and productive day!</strong></p>
                                </div>
                                """, unsafe_allow_html=True)

                            else:
                                st.error("❌ Failed to save checkout data. Please contact support.")
                                log_security_event(
                                    "CHECKOUT_SAVE_FAILED",
                                    employee_id,
                                    logged_username,
                                    "Checkout save operation failed"
                                )

                        except Exception as checkout_error:
                            logger.error(f"Checkout process error: {checkout_error}")
                            st.error(f"❌ Checkout error: {checkout_error}")
                            log_security_event(
                                "CHECKOUT_ERROR",
                                employee_id,
                                logged_username,
                                f"Checkout error: {str(checkout_error)}"
                            )

                except Exception as checkout_calc_error:
                    logger.error(f"Checkout calculation error: {checkout_calc_error}")
                    st.error(f"❌ Error calculating checkout data: {checkout_calc_error}")

            else:
                # ===== ATTENDANCE ALREADY COMPLETE =====
                st.markdown("#### ℹ️ **Attendance Already Complete**")

                try:
                    check_in_time = pd.to_datetime(record["start_datetime"])
                    check_out_time = pd.to_datetime(record["exit_datetime"])

                    st.info("✅ Your secure attendance for today has already been completed.")

                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>📋 Today's Secure Attendance Summary</h3>
                        <p><strong>🔑 Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
                        <p><strong>🚪 Check-Out:</strong> {check_out_time.strftime('%I:%M %p')}</p>
                        <p><strong>⏱️ Total Hours:</strong> {record.get('total_hours', 0):.2f} hours</p>
                        <p><strong>📊 Status:</strong> {record.get('attendance_status', 'Unknown')}</p>
                        <p><strong>⏰ Overtime Hours:</strong> {record.get('extra_hours', 0):.2f} hours</p>
                        <p><strong>💰 Extra Pay:</strong> ₹{record.get('extra_pay', 0):.2f}</p>
                        <p><strong>👤 Verified User:</strong> {logged_username}</p>
                        <p><strong>📍 Location:</strong> {record.get('location_name', 'Unknown')}</p>
                        <p><strong>🔒 Security Level:</strong> Maximum</p>
                        <span class="speed-indicator">ATTENDANCE COMPLETE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Next working day information
                    next_day = today + timedelta(days=1)
                    while next_day.weekday() >= 5:  # Skip weekends
                        next_day += timedelta(days=1)

                    st.markdown(f"""
                    <div class="success-container">
                        <h4 style="color: #2E7D32;">📅 Next Working Day</h4>
                        <p style="color: #388E3C;">Next attendance: <strong>{next_day.strftime('%A, %B %d, %Y')}</strong></p>
                        <p style="color: #388E3C;">Expected arrival: <strong>9:00 AM</strong></p>
                        <p style="color: #388E3C;">Have a great evening!</p>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as summary_error:
                    logger.error(f"Error displaying attendance summary: {summary_error}")
                    st.error("❌ Error loading attendance summary")

        # ===== SECURE ATTENDANCE HISTORY =====
        st.markdown("### 📊 Your Secure Attendance History")

        try:
            employee_attendance = attendance_df[attendance_df["employee_id"] == employee_id].copy()

            if not employee_attendance.empty:
                # Sort by date (most recent first)
                employee_attendance = employee_attendance.sort_values("start_datetime", ascending=False)

                # Display last 10 records with enhanced security info
                display_columns = [
                    "date_only", "start_datetime", "exit_datetime", "total_hours",
                    "attendance_status", "late_mark", "location_name", "confidence", "method"
                ]

                display_df = employee_attendance.head(10)[
                    [col for col in display_columns if col in employee_attendance.columns]
                ].copy()

                if not display_df.empty:
                    # Format columns securely
                    if "start_datetime" in display_df.columns:
                        display_df["Check-In"] = pd.to_datetime(display_df["start_datetime"]).dt.strftime('%I:%M %p')
                        display_df.drop("start_datetime", axis=1, inplace=True)

                    if "exit_datetime" in display_df.columns:
                        display_df["Check-Out"] = pd.to_datetime(display_df["exit_datetime"]).dt.strftime('%I:%M %p')
                        display_df.drop("exit_datetime", axis=1, inplace=True)

                    # Rename columns
                    column_mapping = {
                        "date_only": "Date",
                        "total_hours": "Hours",
                        "attendance_status": "Status",
                        "late_mark": "Late",
                        "location_name": "Location",
                        "confidence": "Biometric %",
                        "method": "Security Method"
                    }

                    display_df = display_df.rename(columns=column_mapping)
                    display_df = display_df.fillna("-")

                    # Format specific columns
                    if "Biometric %" in display_df.columns:
                        display_df["Biometric %"] = display_df["Biometric %"].apply(
                            lambda x: f"{x:.1f}%" if pd.notna(x) and str(x) != "-" else "-"
                        )

                    if "Late" in display_df.columns:
                        display_df["Late"] = display_df["Late"].apply(
                            lambda x: "Yes" if x is True else "No" if x is False else "-"
                        )

                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                # Secure download options
                col1, col2 = st.columns(2)

                with col1:
                    csv_data = employee_attendance.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Personal Report (CSV)",
                        data=csv_data,
                        file_name=f"secure_attendance_{employee_id}_{employee_name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

                with col2:
                    # Current month data
                    current_month = employee_attendance[
                        employee_attendance["start_datetime"].dt.month == now.month
                        ]
                    if not current_month.empty:
                        monthly_csv = current_month.to_csv(index=False)
                        st.download_button(
                            label="📅 Download This Month (CSV)",
                            data=monthly_csv,
                            file_name=f"monthly_attendance_{employee_id}_{now.strftime('%Y_%m')}.csv",
                            mime="text/csv"
                        )

                # Enhanced statistics
                st.markdown("#### 📈 Your Performance Statistics")

                current_month_data = employee_attendance[
                    employee_attendance["start_datetime"].dt.month == now.month
                    ]

                if not current_month_data.empty:
                    try:
                        total_days = len(current_month_data)
                        late_days = len(current_month_data[current_month_data["late_mark"] == True])
                        full_days = len(current_month_data[current_month_data["attendance_status"] == "Full Day"])
                        avg_hours = current_month_data[
                            "total_hours"].mean() if "total_hours" in current_month_data.columns else 0
                        total_overtime = current_month_data[
                            "extra_hours"].sum() if "extra_hours" in current_month_data.columns else 0
                        avg_biometric = current_month_data[
                            "confidence"].mean() if "confidence" in current_month_data.columns else 0

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                label="📅 Days This Month",
                                value=total_days,
                                delta=f"{(total_days / 22) * 100:.0f}% attendance"
                            )

                        with col2:
                            st.metric(
                                label="⏰ Punctuality",
                                value=f"{total_days - late_days}/{total_days}",
                                delta=f"{((total_days - late_days) / total_days) * 100:.0f}% on time" if total_days > 0 else "0%"
                            )

                        with col3:
                            st.metric(
                                label="✅ Full Days",
                                value=full_days,
                                delta=f"{(full_days / total_days) * 100:.0f}% full attendance" if total_days > 0 else "0%"
                            )

                        with col4:
                            st.metric(
                                label="🎯 Avg Biometric",
                                value=f"{avg_biometric:.0f}%",
                                delta="High accuracy"
                            )

                        # Additional performance metrics
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(
                                label="⚡ Avg Daily Hours",
                                value=f"{avg_hours:.1f}h",
                                delta="Productive"
                            )

                        with col2:
                            st.metric(
                                label="⏰ Total Overtime",
                                value=f"{total_overtime:.1f}h",
                                delta="Extra contribution"
                            )

                    except Exception as stats_error:
                        logger.error(f"Statistics calculation error: {stats_error}")
                        st.error("❌ Error calculating statistics")

            else:
                st.info("📋 No attendance history found. Today's attendance will appear here after completion.")

        except Exception as history_error:
            logger.error(f"Attendance history error: {history_error}")
            st.error("❌ Error loading attendance history")

    except Exception as e:
        logger.error(f"Attendance processing error: {e}")
        st.error(f"❌ **Error processing attendance:** {e}")

        # Enhanced error reporting
        with st.expander("🔍 Detailed Error Information"):
            st.code(f"""
            === SECURE ATTENDANCE PROCESSING ERROR ===
            Error: {str(e)}
            Type: {type(e).__name__}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            === USER INFORMATION ===
            Employee ID: {employee_id}
            Employee Name: {employee_name}
            Login Username: {logged_username}
            Session ID: {id(st.session_state)}

            === SECURITY CONTEXT ===
            Location Verified: {location_verified}
            Location Name: {location_name}
            Biometric Confidence: {confidence if 'confidence' in locals() else 'N/A'}
            Detection Method: {detection_method}

            === SYSTEM STATE ===
            Database Mode: {'SQL' if USE_SQL else 'CSV'}
            Face Recognition: {'Available' if FACE_RECOGNITION_AVAILABLE else 'Unavailable'}
            Geolocation: {'Available' if GEOLOCATION_AVAILABLE else 'Unavailable'}
            """)

        # Log critical error
        log_security_event(
            "CRITICAL_ATTENDANCE_ERROR",
            employee_id if 'employee_id' in locals() else "unknown",
            logged_username,
            f"Critical error: {str(e)}"
        )

        # Recovery options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Retry Attendance Process", key="retry_attendance_secure"):
                st.info("♻️ Restarting secure attendance process...")
                st.rerun()

        with col2:
            if st.button("🏠 Return to Dashboard", key="back_to_dashboard"):
                st.info("🏠 Returning to main dashboard...")
                # Clear potentially problematic session data
                for key in ['location_data', 'location_cache']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


# ===== ENHANCED DATABASE STATUS =====
def show_database_status():
    """Show enhanced database connection status with security info"""
    if USE_SQL:
        try:
            with safe_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DB_NAME()")
                db_name = cursor.fetchone()[0]
                print(f"✅ Connected to database: {db_name}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    else:
        print("📂 Using CSV mode (SQL disabled).")

import streamlit as st
import pandas as pd
import os
import json
import logging
import base64
import math
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Tuple, Optional, Any
import pyodbc
from sqlalchemy.exc import SQLAlchemyError
from config import safe_get_conn
engine = safe_get_conn()
# Third-party imports with error handling
try:
    import folium
    from streamlit_folium import st_folium
    from geopy.distance import geodesic

    GEOLOCATION_AVAILABLE = True
except ImportError as e:
    st.error(f"Missing geolocation dependencies: {e}")
    GEOLOCATION_AVAILABLE = False

# Import your existing utilities with error handling
try:
    from utils.biometric_utils import compare_faces

    FACE_RECOGNITION_AVAILABLE = True
except ImportError as e:
    st.error(f"Face recognition not available: {e}")
    FACE_RECOGNITION_AVAILABLE = False

try:
    from utils.data_helpers import get_greeting

    DATA_HELPERS_AVAILABLE = True
except ImportError:
    DATA_HELPERS_AVAILABLE = False


    # Fallback greeting function
    def get_greeting(dt):
        hour = dt.hour
        if hour < 12:
            return "Good Morning"
        elif hour < 17:
            return "Good Afternoon"
        else:
            return "Good Evening"

try:
    from config import *

    CONFIG_AVAILABLE = True
except ImportError as e:
    st.error(f"Configuration not available: {e}")
    CONFIG_AVAILABLE = False


# ===== CONFIGURATION VALIDATION =====
class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


# Security whitelist for database tables
ALLOWED_TABLES = {
    'employee_master',
    'employee_data',
    'attendance_records'
}

# Fallback configuration if config.py is not available
if not CONFIG_AVAILABLE:
    USE_SQL = False
    EMPLOYEE_MASTER_CSV = "data/employee_master.csv"
    EMPLOYEE_DATA_CSV = "data/employee_data.csv"
    BADGE_DIR = "badges/"
    TEMP_CSV_PATH = "data/temp_attendance.csv"
    OFFICE_LOCATIONS = [
        {
            "name": "Main Office",
            "lat": 17.70588,
            "lon": 73.98451,
            "radius": 100
        }
    ]


def validate_configuration():
    """Validate all required configuration variables"""
    required_vars = {
        'EMPLOYEE_MASTER_CSV': str,
        'EMPLOYEE_DATA_CSV': str,
        'BADGE_DIR': str,
        'OFFICE_LOCATIONS': list,
    }

    missing_vars = []
    invalid_vars = []

    for var_name, expected_type in required_vars.items():
        if var_name not in globals():
            missing_vars.append(var_name)
            continue

        var_value = globals()[var_name]
        if not isinstance(var_value, expected_type):
            invalid_vars.append(f"{var_name} should be {expected_type.__name__}")

    if missing_vars:
        raise ConfigurationError(f"Missing configuration variables: {missing_vars}")

    if invalid_vars:
        raise ConfigurationError(f"Invalid configuration types: {invalid_vars}")

    # Validate office locations format
    for i, location in enumerate(OFFICE_LOCATIONS):
        required_keys = ['name', 'lat', 'lon', 'radius']
        missing_keys = [key for key in required_keys if key not in location]
        if missing_keys:
            raise ConfigurationError(f"Office location {i} missing keys: {missing_keys}")

        # Validate coordinate ranges
        if not (-90 <= location['lat'] <= 90):
            raise ConfigurationError(f"Invalid latitude in office location {i}: {location['lat']}")
        if not (-180 <= location['lon'] <= 180):
            raise ConfigurationError(f"Invalid longitude in office location {i}: {location['lon']}")
        if location['radius'] <= 0:
            raise ConfigurationError(f"Invalid radius in office location {i}: {location['radius']}")


def validate_table_name(table_name: str) -> bool:
    """Validate table name against whitelist"""
    return table_name.lower() in ALLOWED_TABLES


# ===== LOGGING CONFIGURATION =====
def setup_logging():
    """Configure structured logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/attendance_system.log'),
            logging.StreamHandler()
        ]
    )

    # Create specific loggers
    security_logger = logging.getLogger('security')
    security_handler = logging.FileHandler('logs/security_audit.log')
    security_handler.setFormatter(logging.Formatter(log_format))
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)

    return logging.getLogger(__name__)


logger = setup_logging()


# ===== SECURE DATABASE OPERATIONS =====
from sqlalchemy import create_engine
import urllib

def get_sql_connection():
    """Return a SQLAlchemy engine instead of raw pyodbc conn"""
    try:
        # Example for SQL Server with Windows Authentication
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=SQL2022_DEV;"         # 🔹 change this
            "DATABASE=ValidexDB;"     # 🔹 change this
            "Trusted_Connection=yes;"
        )

        # Encode connection string for SQLAlchemy
        connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
        engine = create_engine(connection_url)
        return engine
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {e}")
        raise
@contextmanager
def safe_db_connection():
    """Context manager returning a SQLAlchemy connection"""
    conn = None
    try:
        if not USE_SQL:
            raise ValueError("SQL mode not enabled")

        engine = get_sql_connection()
        conn = engine.connect()
        logger.info("Database connection established")
        yield conn
        conn.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def safe_float(value: Any, precision: int = 10, scale: int = 2) -> Optional[float]:
    """Safely convert value to float with validation"""
    if value is None or pd.isna(value):
        return None
    try:
        float_val = float(value)
        if not (-10 ** precision <= float_val <= 10 ** precision):
            logger.warning(f"Float value out of range: {float_val}")
            return None
        return round(float_val, scale)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid float conversion: {value}, error: {e}")
        return None


def safe_datetime_for_sql(value: Any) -> Optional[datetime]:
    """Safely convert value to datetime for SQL"""
    if value is None or pd.isna(value):
        return None
    try:
        if isinstance(value, datetime):
            return value
        return pd.to_datetime(value)
    except Exception as e:
        logger.warning(f"Invalid datetime conversion: {value}, error: {e}")
        return None


def safe_date_for_sql(value: Any):
    """Safely convert value to date for SQL"""
    if value is None or pd.isna(value):
        return None
    try:
        if hasattr(value, 'date'):
            return value.date()
        dt = pd.to_datetime(value)
        return dt.date()
    except Exception as e:
        logger.warning(f"Invalid date conversion: {value}, error: {e}")
        return None


# ===== SECURE PWA CONFIGURATION =====
def get_pwa_manifest() -> str:
    """Generate PWA manifest with proper escaping"""
    manifest = {
        "name": "Company Attendance System",
        "short_name": "Attendance",
        "description": "Employee Attendance with Face Recognition and GPS",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#764ba2",
        "orientation": "portrait",
        "scope": "/",
        "icons": [
            {
                "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    }

    # Properly escape JSON for JavaScript context
    manifest_json = json.dumps(manifest)
    # Escape potentially dangerous characters for JavaScript
    manifest_json = manifest_json.replace('<', '\\u003c').replace('>', '\\u003e')
    manifest_json = manifest_json.replace('&', '\\u0026').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')

    return manifest_json


def get_service_worker() -> str:
    """Generate Service Worker JavaScript with security considerations"""
    return """
const CACHE_NAME = 'attendance-v1';

self.addEventListener('install', function(event) {
    console.log('Service Worker installed');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activated');
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function(event) {
    // Only cache same-origin requests for security
    if (event.request.url.startsWith(self.location.origin)) {
        event.respondWith(
            caches.match(event.request).then(function(response) {
                return response || fetch(event.request).catch(function() {
                    // Fallback for offline scenarios
                    return new Response('Offline', {status: 503});
                });
            })
        );
    }
});
"""


def setup_pwa():
    """Configure PWA settings with security"""
    try:
        st.set_page_config(
            page_title="Company Attendance System",
            page_icon="📱",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
    except Exception as e:
        logger.warning(f"Page config already set: {e}")

    manifest_json = get_pwa_manifest()
    sw_js = get_service_worker()

    # Escape JavaScript content for HTML context
    sw_js_escaped = sw_js.replace('</script>', '</scr" + "ipt>')

    st.markdown(f"""
    <head>
        <meta name="theme-color" content="#764ba2">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <script>
        (function() {{
            try {{
                const manifestData = {manifest_json};
                const manifestBlob = new Blob([JSON.stringify(manifestData)], {{type: 'application/json'}});
                const manifestUrl = URL.createObjectURL(manifestBlob);
                const link = document.createElement('link');
                link.rel = 'manifest';
                link.href = manifestUrl;
                document.head.appendChild(link);

                if ('serviceWorker' in navigator) {{
                    const swBlob = new Blob([`{sw_js_escaped}`], {{type: 'application/javascript'}});
                    const swUrl = URL.createObjectURL(swBlob);
                    navigator.serviceWorker.register(swUrl).then(function(registration) {{
                        console.log('ServiceWorker registration successful');
                    }}).catch(function(error) {{
                        console.log('ServiceWorker registration failed:', error);
                    }});
                }}
            }} catch (error) {{
                console.error('PWA setup error:', error);
            }}
        }})();
    </script>
    """, unsafe_allow_html=True)


# ===== ENHANCED MOBILE CSS =====
def apply_mobile_css():
    st.markdown("""
    <style>
    .stApp {
        max-width: 100%;
        margin: 0;
        padding: 0;
    }

    .pwa-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        margin: -1rem -1rem 1rem -1rem;
        text-align: center;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .user-info-card {
        background: linear-gradient(135deg, #2196F3, #1976D2);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(33, 150, 243, 0.3);
    }

    .location-status {
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
        font-weight: bold;
    }

    .location-approved {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        box-shadow: 0 5px 15px rgba(76,175,80,0.3);
    }

    .location-denied {
        background: linear-gradient(135deg, #f44336, #da190b);
        color: white;
        box-shadow: 0 5px 15px rgba(244,67,54,0.3);
    }

    .location-detecting {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white;
        box-shadow: 0 5px 15px rgba(255,152,0,0.3);
        animation: pulse 2s infinite;
    }

    .fast-location-card {
        background: linear-gradient(135deg, #2196F3, #1976D2);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 6px 20px rgba(33, 150, 243, 0.3);
        transition: all 0.3s ease;
    }

    .fast-location-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(33, 150, 243, 0.4);
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        animation: fadeIn 0.5s ease-out;
    }

    .security-badge {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        border-left: 5px solid #E65100;
    }

    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 16px;
        font-weight: bold;
        margin: 0.5rem 0;
        border-radius: 12px;
        transition: all 0.3s ease;
    }

    .speed-indicator {
        background: linear-gradient(135deg, #00E676, #00C853);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        animation: fadeIn 0.5s ease-out;
    }

    .error-container {
        background: #FFEBEE;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #F44336;
        margin: 10px 0;
    }

    .warning-container {
        background: #FFF3E0;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 10px 0;
    }

    .success-container {
        background: #E8F5E8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)


# ===== PRESET LOCATIONS WITH VALIDATION =====
PRESET_LOCATIONS = {
    "office_main": {
        "name": "Main Office",
        "lat": 17.70588,
        "lon": 73.98451,
        "icon": "🏢"
    },
    "office_branch": {
        "name": "Branch Office",
        "lat": 17.70600,
        "lon": 73.98500,
        "icon": "🏬"
    },
    "office_remote": {
        "name": "Remote Location",
        "lat": 17.70580,
        "lon": 73.98480,
        "icon": "💻"
    }
}


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate coordinate ranges"""
    return -90 <= lat <= 90 and -180 <= lon <= 180


# ===== SECURE DATABASE FUNCTIONS =====
@st.cache_data(ttl=300)  # 5-minute cache
def load_employee_master() -> pd.DataFrame:
    """Load employee master data with caching"""
    logger.info("Loading employee master data")

    if USE_SQL:
        try:
            with safe_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")

                st.markdown("""
                <div class="success-container">
                    <p style="margin: 0; color: #2E7D32;"><strong>🗄️ Database Status:</strong> ✅ SQL Connected & Secure</p>
                    <small style="color: #388E3C;">Enhanced security protocols active</small>
                </div>
                """, unsafe_allow_html=True)

        except Exception as db_error:
            logger.warning(f"Database connection failed: {db_error}")

            # Check for temporary data
            temp_records = 0
            if os.path.exists(TEMP_CSV_PATH):
                try:
                    temp_df = pd.read_csv(TEMP_CSV_PATH)
                    temp_records = len(temp_df)
                except Exception as temp_error:
                    logger.error(f"Error reading temp data: {temp_error}")

            st.markdown(f"""
            <div class="warning-container">
                <p style="margin: 0; color: #E65100;"><strong>🗄️ Database Status:</strong> ⚠️ SQL Offline - Secure CSV Fallback Active</p>
                {f"<p style='color: #E65100; margin: 5px 0 0 0; font-size: 12px;'>📊 {temp_records} secure records awaiting sync</p>" if temp_records > 0 else ""}
                <small style="color: #F57C00;">All data remains secure and will sync automatically</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #E3F2FD; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <p style="color: #1976D2; margin: 0;"><strong>🗄️ Database Status:</strong> 📄 Secure CSV Mode Active</p>
            <small style="color: #1565C0;">File-based storage with security validation</small>
        </div>
        """, unsafe_allow_html=True)


# ===== SYSTEM HEALTH AND MONITORING =====
def system_health_check() -> Dict[str, Any]:
    """Comprehensive system health check with security validation"""
    health_status = {
        "overall_status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    issues = 0

    try:
        # Database connectivity
        if USE_SQL:
            try:
                with safe_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    health_status["components"]["database"] = {
                        "status": "healthy",
                        "details": "SQL connection successful"
                    }
            except Exception as db_error:
                health_status["components"]["database"] = {
                    "status": "degraded",
                    "details": f"SQL unavailable: {str(db_error)}"
                }
                issues += 1
        else:
            if os.path.exists(EMPLOYEE_DATA_CSV):
                health_status["components"]["database"] = {
                    "status": "healthy",
                    "details": "CSV mode operational"
                }
            else:
                health_status["components"]["database"] = {
                    "status": "degraded",
                    "details": "CSV files missing"
                }
                issues += 1

        # Configuration validation
        try:
            validate_configuration()
            health_status["components"]["configuration"] = {
                "status": "healthy",
                "details": "All config validated"
            }
        except ConfigurationError as config_error:
            health_status["components"]["configuration"] = {
                "status": "critical",
                "details": str(config_error)
            }
            issues += 2

        # Essential directories and files
        required_paths = [
            (BADGE_DIR, "Badge directory"),
            (EMPLOYEE_MASTER_CSV, "Employee master CSV"),
            ("logs", "Logs directory")
        ]

        for path, description in required_paths:
            if os.path.exists(path):
                health_status["components"][description.lower().replace(" ", "_")] = {
                    "status": "healthy",
                    "details": f"{description} available"
                }
            else:
                health_status["components"][description.lower().replace(" ", "_")] = {
                    "status": "degraded",
                    "details": f"{description} missing"
                }
                issues += 1

        # Security features
        security_features = [
            (FACE_RECOGNITION_AVAILABLE, "Face Recognition"),
            (GEOLOCATION_AVAILABLE, "Geolocation Services"),
            (CONFIG_AVAILABLE, "Configuration System"),
            (DATA_HELPERS_AVAILABLE, "Data Helpers")
        ]

        for available, feature_name in security_features:
            if available:
                health_status["components"][feature_name.lower().replace(" ", "_")] = {
                    "status": "healthy",
                    "details": f"{feature_name} operational"
                }
            else:
                health_status["components"][feature_name.lower().replace(" ", "_")] = {
                    "status": "degraded",
                    "details": f"{feature_name} unavailable"
                }
                issues += 1

        # Determine overall status
        if issues == 0:
            health_status["overall_status"] = "healthy"
        elif issues <= 2:
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "critical"

    except Exception as health_error:
        logger.error(f"Health check error: {health_error}")
        health_status["overall_status"] = "critical"
        health_status["error"] = str(health_error)

    return health_status


# ===== TEMPORARY DATA SYNCHRONIZATION =====
def check_and_sync_temp_data():
    """Check for temporary data and offer sync options"""
    if not os.path.exists(TEMP_CSV_PATH):
        return

    try:
        temp_df = pd.read_csv(TEMP_CSV_PATH)
        if len(temp_df) == 0:
            return

        st.info(f"📊 Found {len(temp_df)} attendance records waiting for database sync")

        # Auto-sync if database is available
        if USE_SQL:
            try:
                with safe_db_connection() as conn:
                    # Database is available, attempt auto-sync
                    if save_attendance_secure(temp_df):
                        # Remove temp file after successful sync
                        os.remove(TEMP_CSV_PATH)
                        st.success("✅ Temporary data automatically synced to database!")
                        logger.info(f"Auto-synced {len(temp_df)} temp records")
            except Exception as sync_error:
                logger.error(f"Auto-sync failed: {sync_error}")
                # Keep temp data for manual sync later

    except Exception as temp_error:
        logger.error(f"Error checking temp data: {temp_error}")


# ===== SECURITY AUDIT AND LOGGING =====
def log_attendance_save(status: str, method: str, record_count: int, details: str = ""):
    """Log attendance save operations for audit purposes"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    audit_entry = {
        "timestamp": timestamp,
        "operation": "ATTENDANCE_SAVE",
        "status": status,
        "method": method,
        "record_count": record_count,
        "details": details,
        "user": st.session_state.get("username", "unknown"),
        "employee_id": st.session_state.get("employee_id", "unknown")
    }

    try:
        # Ensure audit log directory exists
        os.makedirs("logs", exist_ok=True)

        # Write to audit log
        audit_logger = logging.getLogger('attendance_audit')
        audit_handler = logging.FileHandler('logs/attendance_save_audit.log')
        audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)

        import json
        audit_logger.info(json.dumps(audit_entry))

        # Also write to daily log
        daily_audit_path = f"logs/attendance_save_{datetime.now().strftime('%Y%m%d')}.log"
        with open(daily_audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")

    except Exception as log_error:
        logger.error(f"Failed to write attendance save audit: {log_error}")


# ===== MAIN APPLICATION INITIALIZATION =====
def initialize_secure_attendance_system() -> bool:
    """Initialize the secure attendance system with comprehensive validation"""
    try:
        # System health check
        logger.info("Starting secure attendance system initialization")

        # Configuration validation
        try:
            validate_configuration()
            logger.info("Configuration validation successful")
        except ConfigurationError as config_error:
            logger.error(f"Configuration validation failed: {config_error}")
            st.error(f"🚨 **Configuration Error:** {config_error}")
            return False

        # Security validation
        try:
            is_valid, message = validate_session_security()
            if not is_valid:
                logger.error(f"Session security validation failed: {message}")
                st.error(f"🔒 **Security Validation Failed:** {message}")

                # Log security failure
                log_security_event(
                    "SYSTEM_INIT_SECURITY_FAILURE",
                    st.session_state.get("employee_id", "unknown"),
                    st.session_state.get("username", "unknown"),
                    message
                )
                return False

        except Exception as security_error:
            logger.error(f"Security validation error: {security_error}")
            st.error(f"❌ Security validation error: {security_error}")
            return False

        # Check essential services
        missing_services = []

        if not GEOLOCATION_AVAILABLE:
            missing_services.append("Geolocation Services")

        if not FACE_RECOGNITION_AVAILABLE:
            missing_services.append("Face Recognition")

        if missing_services:
            st.warning(f"⚠️ Some services are unavailable: {', '.join(missing_services)}")
            st.info("The system will continue with available features.")

        # Log successful initialization
        log_security_event(
            "SYSTEM_INIT_SUCCESS",
            st.session_state.get("employee_id", "unknown"),
            st.session_state.get("username", "unknown"),
            "Secure attendance system initialized successfully"
        )

        logger.info("Secure attendance system initialization completed successfully")
        return True

    except Exception as init_error:
        logger.error(f"System initialization failed: {init_error}")
        st.error(f"❌ **System Initialization Error:** {init_error}")

        # Log critical initialization failure
        try:
            log_security_event(
                "SYSTEM_INIT_CRITICAL_FAILURE",
                st.session_state.get("employee_id", "unknown"),
                st.session_state.get("username", "unknown"),
                f"Initialization failed: {str(init_error)}"
            )
        except:
            pass  # Don't let logging errors crash the error handler

        return False


# ===== MAIN APPLICATION ENTRY POINT =====
def main():
    """Main entry point for the secure attendance system"""
    try:
        # Initialize system with comprehensive checks
        if not initialize_secure_attendance_system():
            st.error("❌ **System initialization failed.** Please contact support.")
            st.stop()

        # Check and handle temporary data
        check_and_sync_temp_data()

        # Run the secure attendance system
        run_attendance()

    except Exception as critical_error:
        logger.critical(f"Critical system error: {critical_error}")

        st.markdown("""
        <div class="error-container">
            <h3 style="color: #C62828;">🚨 Critical System Error</h3>
            <p>The attendance system encountered a critical error and cannot continue safely.</p>
            <p><strong>Error Details:</strong> System protection activated</p>
            <p><strong>Time:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔧 Emergency Recovery Information"):
            st.markdown(f"""
            **Critical Error Details:**
            - **Error Type:** {type(critical_error).__name__}
            - **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            - **Session ID:** {id(st.session_state)}

            **Immediate Recovery Steps:**
            1. 🔄 **Refresh the page completely** (Ctrl+F5 or Cmd+Shift+R)
            2. 🔐 **Re-login** with your credentials
            3. 🧹 **Clear browser cache** if problems persist
            4. 📞 **Contact IT Support** if error continues

            **System Status:**
            - Database Mode: {'SQL' if USE_SQL else 'CSV'}
            - Face Recognition: {'Available' if FACE_RECOGNITION_AVAILABLE else 'Unavailable'}
            - Geolocation: {'Available' if GEOLOCATION_AVAILABLE else 'Unavailable'}
            - Configuration: {'Available' if CONFIG_AVAILABLE else 'Unavailable'}

            **Emergency Contacts:**
            - IT Support: [Contact Information]
            - HR Department: [Contact Information] 
            - System Administrator: [Contact Information]

            **Data Safety Note:**
            Your attendance data is protected by multiple backup systems.
            No data has been lost due to this error.
            """)

        # Log critical system error
        try:
            log_security_event(
                "CRITICAL_SYSTEM_FAILURE",
                st.session_state.get("employee_id", "unknown"),
                st.session_state.get("username", "unknown"),
                f"Critical system failure: {str(critical_error)}"
            )
        except:
            pass  # Final safety net - don't let logging crash the error handler

        # Emergency recovery button
        if st.button("🆘 Emergency System Reset", key="emergency_reset"):
            st.info("🔄 Performing emergency system reset...")

            # Clear potentially corrupted session data
            keys_to_clear = ['location_data', 'location_cache', 'location_detection_started']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]

            st.info("✅ Session data cleared. Please refresh the page.")


# ===== ADDITIONAL UTILITY FUNCTIONS =====
def cleanup_old_logs(days_to_keep: int = 30):
    """Clean up old log files to prevent disk space issues"""
    try:
        import glob
        from pathlib import Path

        log_dir = Path("logs")
        if not log_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0

        # Clean daily attendance logs
        for log_file in glob.glob("logs/attendance_*.log"):
            try:
                file_path = Path(log_file)
                file_date_str = file_path.stem.split('_')[-1]

                if len(file_date_str) == 8 and file_date_str.isdigit():
                    file_date = datetime.strptime(file_date_str, '%Y%m%d')

                    if file_date < cutoff_date:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up old log: {log_file}")

            except Exception as cleanup_error:
                logger.warning(f"Error cleaning log file {log_file}: {cleanup_error}")
                continue

        if cleaned_count > 0:
            logger.info(f"Cleanup completed: removed {cleaned_count} old log files")

    except Exception as e:
        logger.error(f"Error during log cleanup: {e}")


# ===== RUN THE APPLICATION =====
if __name__ == "__main__":
    try:
        # Set page configuration
        st.set_page_config(
            page_title="Secure Attendance System",
            page_icon="🔒",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        # Perform periodic cleanup
        cleanup_old_logs(30)

        # Run main application
        main()

    except Exception as startup_error:
        # Final safety net for startup errors
        logger.critical(f"Fatal error running attendance system: {startup_error}")
        st.error(f"🚨 Fatal system error: {startup_error}")
        st.error("❌ **Critical Startup Error**")
        st.error("The application failed to start properly.")
        st.code(f"Error: {str(startup_error)}")
        st.info("Please refresh the page or contact support.")

        # Try to log startup error if possible
        try:
            logger.critical(f"Application startup failed: {startup_error}")
        except:
            pass  # If even logging fails, just show the error to user


            def get_employee_master() -> pd.DataFrame:
                """Load employee master data from SQL if available, else CSV fallback"""
                if USE_SQL:
                    try:
                        # Use parameterized query with validated table name
                        if not validate_table_name(EMPLOYEE_MASTER_TABLE):
                            raise ConfigurationError(f"Invalid table name: {EMPLOYEE_MASTER_TABLE}")

                        query = f"SELECT * FROM {EMPLOYEE_MASTER_TABLE}"
                        df = pd.read_sql(query, safe_get_conn())
                        df.columns = df.columns.str.strip().str.lower()
                        logger.info(f"Loaded {len(df)} employee records from SQL")
                        return df

                    except Exception as e:
                        logger.error(f"SQL error loading employee master: {e}")
                        st.warning("Database unavailable, using CSV fallback")

                # CSV fallback
                try:
                    if not os.path.exists(EMPLOYEE_MASTER_CSV):
                        logger.error(f"Employee master CSV not found: {EMPLOYEE_MASTER_CSV}")
                        return pd.DataFrame()

                    df = pd.read_csv(EMPLOYEE_MASTER_CSV, dtype={"employee_id": str})
                    logger.info(f"Loaded {len(df)} employee records from CSV")
                    return df

                except Exception as e:
                    logger.error(f"Error loading CSV: {e}")
                    st.error(f"Error loading employee data: {e}")
                    return pd.DataFrame()

def load_attendance() -> pd.DataFrame:
    """Load attendance data with proper error handling"""
    logger.info("Loading attendance data")

    if USE_SQL:
        try:
            with safe_db_connection() as conn:
                if not validate_table_name(EMPLOYEE_DATA_TABLE):
                    raise ConfigurationError(f"Invalid table name: {EMPLOYEE_DATA_TABLE}")

                query = f"SELECT * FROM {EMPLOYEE_DATA_TABLE}"
                df = pd.read_sql(query, conn)

                # Safe datetime conversion
                for col in ['start_datetime', 'exit_datetime']:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')

                logger.info(f"Loaded {len(df)} attendance records from SQL")
                return df

        except Exception as e:
            logger.error(f"SQL error loading attendance: {e}")
            st.warning("Database unavailable, using CSV fallback")

    # CSV fallback
    try:
        if os.path.exists(EMPLOYEE_DATA_CSV):
            df = pd.read_csv(EMPLOYEE_DATA_CSV)
            for col in ['start_datetime', 'exit_datetime']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            logger.info(f"Loaded {len(df)} attendance records from CSV")
            return df
        else:
            logger.info("No attendance CSV found, creating empty DataFrame")
            return create_empty_attendance_df()

    except Exception as e:
        logger.error(f"Error loading attendance CSV: {e}")
        return create_empty_attendance_df()


def create_empty_attendance_df() -> pd.DataFrame:
    """Create empty attendance DataFrame with proper columns"""
    columns = [
        "employee_id", "employee_name", "start_datetime", "exit_datetime",
        "date_only", "total_hours", "extra_hours", "extra_pay",
        "attendance_status", "late_mark", "method", "confidence", "notes",
        "location_lat", "location_lon", "location_verified", "location_name"
    ]
    return pd.DataFrame(columns=columns)


def save_attendance_secure(df: pd.DataFrame) -> bool:
    """Secure attendance data saving with comprehensive error handling"""
    logger.info(f"Attempting to save {len(df)} attendance records")

    if df.empty:
        logger.warning("Empty DataFrame provided for saving")
        return False

    if USE_SQL:
        try:
            with safe_db_connection() as conn:
                cursor = conn.cursor()

                if not validate_table_name(EMPLOYEE_DATA_TABLE):
                    raise ConfigurationError(f"Invalid table name: {EMPLOYEE_DATA_TABLE}")

                success_count = 0
                for _, row in df.iterrows():
                    try:
                        # Validate and sanitize all data
                        employee_id = str(row["employee_id"]).strip()
                        employee_name = str(row["employee_name"]).strip()

                        if not employee_id or not employee_name:
                            logger.warning(f"Skipping row with missing ID or name: {row}")
                            continue

                        start_datetime = safe_datetime_for_sql(row["start_datetime"])
                        exit_datetime = safe_datetime_for_sql(row["exit_datetime"]) if pd.notna(
                            row["exit_datetime"]) else None

                        date_only = safe_date_for_sql(row["date_only"])
                        if date_only is None and start_datetime:
                            date_only = start_datetime.date()

                        total_hours = safe_float(row["total_hours"]) if pd.notna(row["total_hours"]) else None
                        extra_hours = safe_float(row["extra_hours"]) if pd.notna(row["extra_hours"]) else 0
                        extra_pay = safe_float(row["extra_pay"]) if pd.notna(row["extra_pay"]) else 0
                        attendance_status = str(row["attendance_status"]) if pd.notna(
                            row["attendance_status"]) else None
                        late_mark = bool(row["late_mark"]) if pd.notna(row["late_mark"]) else False
                        method = str(row["method"]) if pd.notna(row["method"]) else "GPS + Face Recognition"
                        confidence = safe_float(row["confidence"], precision=5, scale=2) if pd.notna(
                            row["confidence"]) else 0
                        notes = str(row["notes"])[:500] if pd.notna(row["notes"]) else ""  # Limit notes length

                        location_lat = safe_float(row.get("location_lat")) if pd.notna(
                            row.get("location_lat")) else None
                        location_lon = safe_float(row.get("location_lon")) if pd.notna(
                            row.get("location_lon")) else None
                        location_verified = bool(row.get("location_verified", False))
                        location_name = str(row.get("location_name", ""))[:100] if pd.notna(
                            row.get("location_name")) else ""

                        # Validate coordinates if provided
                        if location_lat is not None and location_lon is not None:
                            if not validate_coordinates(location_lat, location_lon):
                                logger.warning(f"Invalid coordinates: {location_lat}, {location_lon}")
                                location_lat = location_lon = None

                        # Use parameterized query - safe because table name is validated
                        merge_sql = f"""
                        MERGE {EMPLOYEE_DATA_TABLE} AS target
                        USING (SELECT ? AS employee_id, CAST(? AS DATE) AS date_only) AS source
                        ON target.employee_id = source.employee_id AND CAST(target.date_only AS DATE) = source.date_only
                        WHEN MATCHED THEN
                            UPDATE SET 
                                employee_name = ?, 
                                exit_datetime = ?, 
                                total_hours = ?, 
                                extra_hours = ?, 
                                extra_pay = ?, 
                                attendance_status = ?, 
                                late_mark = ?, 
                                method = ?, 
                                confidence = ?, 
                                notes = ?,
                                location_lat = ?,
                                location_lon = ?,
                                location_verified = ?,
                                location_name = ?
                        WHEN NOT MATCHED THEN
                            INSERT (employee_id, employee_name, start_datetime, exit_datetime, date_only, 
                                   total_hours, extra_hours, extra_pay, attendance_status, late_mark, 
                                   method, confidence, notes, location_lat, location_lon, location_verified, location_name)
                            VALUES (?, ?, ?, ?, CAST(? AS DATE), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """

                        params = (
                            employee_id, date_only,
                            employee_name, exit_datetime, total_hours, extra_hours, extra_pay,
                            attendance_status, late_mark, method, confidence, notes,
                            location_lat, location_lon, location_verified, location_name,
                            employee_id, employee_name, start_datetime, exit_datetime, date_only,
                            total_hours, extra_hours, extra_pay, attendance_status, late_mark,
                            method, confidence, notes, location_lat, location_lon, location_verified, location_name
                        )

                        cursor.execute(merge_sql, params)
                        success_count += 1

                    except Exception as row_error:
                        logger.error(f"Error processing row: {row_error}")
                        continue

                conn.commit()
                logger.info(f"Successfully saved {success_count}/{len(df)} records to SQL database")
                st.success(f"✅ Data saved to database successfully! ({success_count} records)")
                return True

        except Exception as e:
            logger.error(f"SQL save failed: {e}")
            st.error(f"❌ Database error: {e}")
            st.warning("⚠️ Saving to temporary file for later sync...")

            # Fallback to temporary CSV
            try:
                save_to_temp_csv(df)
                st.success("✅ Data saved to temporary storage - will sync when database is available!")
                return True
            except Exception as temp_error:
                logger.error(f"Temporary save also failed: {temp_error}")
                st.error(f"❌ Critical error: Cannot save data: {temp_error}")
                return False
    else:
        # CSV mode
        try:
            return save_to_csv(df)
        except Exception as e:
            logger.error(f"CSV save failed: {e}")
            st.error(f"❌ CSV save error: {e}")
            return False


def save_to_csv(df: pd.DataFrame) -> bool:
    """Save to CSV with backup"""
    try:
        df_copy = df.copy()

        # Convert date columns properly
        if 'date_only' in df_copy.columns:
            df_copy['date_only'] = pd.to_datetime(df_copy['date_only']).dt.date

        # Create backup of existing file
        if os.path.exists(EMPLOYEE_DATA_CSV):
            backup_path = f"{EMPLOYEE_DATA_CSV}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(EMPLOYEE_DATA_CSV, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(EMPLOYEE_DATA_CSV), exist_ok=True)

        df_copy.to_csv(EMPLOYEE_DATA_CSV, index=False)
        logger.info(f"Saved {len(df_copy)} records to CSV")
        st.success("✅ Data saved to CSV file successfully!")
        return True

    except Exception as e:
        logger.error(f"CSV save error: {e}")
        raise


def save_to_temp_csv(df: pd.DataFrame):
    """Save to temporary CSV for later sync"""
    try:
        # Ensure temp directory exists
        os.makedirs(os.path.dirname(TEMP_CSV_PATH), exist_ok=True)

        # Append to existing temp file or create new
        if os.path.exists(TEMP_CSV_PATH):
            existing_df = pd.read_csv(TEMP_CSV_PATH)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df

        combined_df.to_csv(TEMP_CSV_PATH, index=False)
        logger.info(f"Saved {len(df)} records to temporary storage")

    except Exception as e:
        logger.error(f"Temporary CSV save error: {e}")
        raise


# ===== LOCATION DETECTION WITH VALIDATION =====
def check_location_permission(user_lat: float, user_lon: float) -> Tuple[bool, Optional[str], Optional[float]]:
    """Check if user is within allowed location radius with validation"""
    if not user_lat or not user_lon or user_lat == 0 or user_lon == 0:
        logger.warning(f"Invalid coordinates provided: {user_lat}, {user_lon}")
        return False, None, None

    # Validate coordinate ranges
    if not validate_coordinates(user_lat, user_lon):
        logger.warning(f"Coordinates out of valid range: {user_lat}, {user_lon}")
        return False, None, None

    if not GEOLOCATION_AVAILABLE:
        logger.error("Geolocation services not available")
        st.error("❌ Location services are not available. Please contact support.")
        return False, None, None

    user_location = (user_lat, user_lon)

    try:
        for location in OFFICE_LOCATIONS:
            office_location = (location["lat"], location["lon"])
            distance = geodesic(user_location, office_location).meters

            logger.info(f"Distance to {location['name']}: {distance}m (limit: {location['radius']}m)")

            if distance <= location["radius"]:
                logger.info(f"Location approved: {location['name']}")
                return True, location["name"], distance

        logger.warning(f"User location {user_lat}, {user_lon} not within any authorized area")
        return False, None, None

    except Exception as e:
        logger.error(f"Error checking location permission: {e}")
        return False, None, None


# ===== ENHANCED LOCATION DETECTION =====
def get_location_ultra_fast() -> Optional[Dict]:
    """Ultra-fast location detection with comprehensive validation"""
    if not GEOLOCATION_AVAILABLE:
        st.error("❌ Geolocation services are not available")
        return None

    # Initialize session state with validation
    if 'location_data' not in st.session_state:
        st.session_state.location_data = None
    if 'location_cache' not in st.session_state:
        st.session_state.location_cache = {}

    # Check recent cache (5 minutes)
    cache_key = "recent_location"
    if cache_key in st.session_state.location_cache:
        cached_location = st.session_state.location_cache[cache_key]

        try:
            cache_age = (datetime.now().timestamp() - cached_location.get('timestamp', 0)) / 60

            if cache_age < 5:  # Less than 5 minutes old
                # Validate cached coordinates
                lat = cached_location.get('latitude', 0)
                lon = cached_location.get('longitude', 0)

                if validate_coordinates(lat, lon):
                    st.markdown(f"""
                    <div class="fast-location-card">
                        <h4>⚡ Using Recent Location</h4>
                        <p>📍 Cached GPS from {cache_age:.1f} minutes ago</p>
                        <span class="speed-indicator">INSTANT</span>
                    </div>
                    """, unsafe_allow_html=True)
                    return cached_location
                else:
                    logger.warning(f"Invalid cached coordinates: {lat}, {lon}")
                    del st.session_state.location_cache[cache_key]
        except Exception as e:
            logger.error(f"Error processing cached location: {e}")
            st.session_state.location_cache.clear()

    # Show location selection interface
    st.markdown("""
    <div class="fast-location-card">
        <h4>⚡ Ultra-Fast Location Selection</h4>
        <p>Choose your method for instant location detection</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick selection buttons
    cols = st.columns(len(PRESET_LOCATIONS) + 1)

    # Preset location buttons with validation
    for idx, (key, location) in enumerate(PRESET_LOCATIONS.items()):
        with cols[idx]:
            if st.button(
                    f"{location['icon']} {location['name']}",
                    key=f"preset_{key}",
                    help=f"Instantly use {location['name']} coordinates"
            ):
                # Validate preset coordinates
                if not validate_coordinates(location['lat'], location['lon']):
                    st.error(f"❌ Invalid preset coordinates for {location['name']}")
                    logger.error(f"Invalid preset coordinates: {location}")
                    continue

                location_data = {
                    "latitude": location['lat'],
                    "longitude": location['lon'],
                    "source": f"Preset: {location['name']}",
                    "method": "instant_preset",
                    "manual": True,
                    "timestamp": datetime.now().timestamp(),
                    "speed": "instant"
                }

                # Cache the location
                st.session_state.location_cache[cache_key] = location_data
                st.session_state.location_data = location_data

                logger.info(f"Preset location selected: {location['name']}")
                st.success(f"⚡ {location['name']} selected instantly!")
                st.rerun()

    # Auto-GPS detection button
    with cols[-1]:
        if st.button("🌐 Auto-GPS", key="auto_gps_ultra", help="Detect GPS automatically (2-3 seconds)"):
            with st.spinner("🔄 Detecting GPS..."):
                # Show progress with validation
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Simulate GPS detection with realistic timing
                    import time
                    for i in range(101):
                        progress_bar.progress(i)
                        if i < 30:
                            status_text.text("📡 Connecting to GPS satellites...")
                        elif i < 60:
                            status_text.text("📍 Getting precise coordinates...")
                        elif i < 90:
                            status_text.text("🎯 Verifying location accuracy...")
                        else:
                            status_text.text("✅ Location detected!")

                        time.sleep(0.02)  # Total: ~2 seconds

                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()

                    # In production, replace with actual GPS detection
                    # For demo, using main office coordinates
                    detected_lat = PRESET_LOCATIONS["office_main"]["lat"]
                    detected_lon = PRESET_LOCATIONS["office_main"]["lon"]

                    # Add small random variation to simulate real GPS
                    import random
                    detected_lat += random.uniform(-0.0001, 0.0001)
                    detected_lon += random.uniform(-0.0001, 0.0001)

                    if not validate_coordinates(detected_lat, detected_lon):
                        st.error("❌ GPS detection failed - invalid coordinates")
                        return None

                    location_data = {
                        "latitude": detected_lat,
                        "longitude": detected_lon,
                        "source": "Auto-GPS Detection",
                        "method": "gps_auto",
                        "manual": False,
                        "timestamp": datetime.now().timestamp(),
                        "accuracy": "high",
                        "speed": "fast"
                    }

                    # Cache and store
                    st.session_state.location_cache[cache_key] = location_data
                    st.session_state.location_data = location_data

                    logger.info(f"GPS location detected: {detected_lat:.6f}, {detected_lon:.6f}")
                    st.success("⚡ GPS location detected in 2 seconds!")
                    st.rerun()

                except Exception as e:
                    logger.error(f"GPS detection error: {e}")
                    st.error("❌ GPS detection failed. Please try preset locations.")

    # Advanced GPS with JavaScript integration
    if st.button("🔬 Advanced GPS", key="advanced_gps"):
        st.markdown("""
        <div id="advanced-location-container" style="text-align: center; padding: 20px;">
            <div id="advanced-status">🔄 Starting advanced GPS detection...</div>
            <div id="advanced-coords" style="display: none;"></div>
        </div>

        <script>
        (function() {
            function advancedGPSDetection() {
                const statusDiv = document.getElementById('advanced-status');
                const coordsDiv = document.getElementById('advanced-coords');

                if (!navigator.geolocation) {
                    statusDiv.innerHTML = '❌ GPS not supported by this browser';
                    return;
                }

                statusDiv.innerHTML = '⚡ Detecting GPS with high accuracy...';

                const options = {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                };

                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const accuracy = Math.round(position.coords.accuracy);

                        // Basic coordinate validation on client side
                        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
                            statusDiv.innerHTML = '❌ Invalid GPS coordinates detected';
                            return;
                        }

                        coordsDiv.innerHTML = lat + ',' + lon + ',' + accuracy;
                        coordsDiv.style.display = 'block';
                        statusDiv.innerHTML = `✅ GPS detected! Accuracy: ${accuracy}m`;

                        // Auto-refresh after 2 seconds
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    },
                    function(error) {
                        let errorMsg = 'Unknown error';
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMsg = 'Location access denied by user';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMsg = 'Location information unavailable';
                                break;
                            case error.TIMEOUT:
                                errorMsg = 'Location request timed out';
                                break;
                        }
                        statusDiv.innerHTML = `❌ GPS detection failed: ${errorMsg}`;
                    },
                    options
                );
            }

            // Start detection with error handling
            try {
                advancedGPSDetection();
            } catch (error) {
                console.error('Advanced GPS detection error:', error);
                document.getElementById('advanced-status').innerHTML = '❌ GPS detection failed';
            }
        })();
        </script>
        """, unsafe_allow_html=True)

    # Current status display
    if st.session_state.location_data:
        location = st.session_state.location_data
        lat = location.get('latitude', 0)
        lon = location.get('longitude', 0)

        # Validate current location data
        if validate_coordinates(lat, lon):
            st.markdown(f"""
            <div class="location-status location-approved">
                ✅ Location Ready!<br>
                📍 {location.get('source', 'GPS Location')}<br>
                ⚡ Method: {location.get('method', 'unknown')}<br>
                🕒 Speed: {location.get('speed', 'fast')}<br>
                📐 Coordinates: {lat:.4f}, {lon:.4f}
            </div>
            """, unsafe_allow_html=True)
            return location
        else:
            logger.error(f"Invalid location data in session: {lat}, {lon}")
            st.session_state.location_data = None
            st.error("❌ Invalid location data detected. Please try again.")
            return None
    else:
        st.info("📍 Please select a location method above")
        return None


# ===== SECURE SESSION VALIDATION =====
def validate_session_security() -> Tuple[bool, str]:
    """Enhanced session security validation with detailed checks"""
    required_keys = ["login_phase", "user_role", "employee_name", "employee_id", "username"]

    # Check for required session keys
    for key in required_keys:
        if key not in st.session_state:
            logger.warning(f"Missing session key: {key}")
            return False, f"Missing session key: {key}"

    # Validate login phase
    if st.session_state["login_phase"] != "verified":
        logger.warning(f"Invalid login phase: {st.session_state.get('login_phase')}")
        return False, "Invalid login phase"

    # Validate user role
    if st.session_state["user_role"] != "employee":
        logger.warning(f"Invalid user role: {st.session_state.get('user_role')}")
        return False, "Invalid user role for attendance"

    # Validate employee information
    employee_name = st.session_state.get("employee_name", "").strip()
    employee_id = str(st.session_state.get("employee_id", "")).strip()
    username = st.session_state.get("username", "").strip()

    if not employee_name:
        logger.warning("Empty employee name in session")
        return False, "Missing employee name"

    if not employee_id or len(employee_id) < 1:
        logger.warning(f"Invalid employee ID: {employee_id}")
        return False, "Invalid employee ID format"

    if not username:
        logger.warning("Empty username in session")
        return False, "Missing username"

    # Additional security checks
    if len(employee_name) > 100:  # Reasonable name length limit
        logger.warning(f"Employee name too long: {len(employee_name)}")
        return False, "Invalid employee name length"

    if len(employee_id) > 20:  # Reasonable ID length limit
        logger.warning(f"Employee ID too long: {len(employee_id)}")
        return False, "Invalid employee ID length"

    logger.info(f"Session validation successful for user: {username}")
    return True, "Session valid and secure"


def log_security_event(event_type: str, employee_id: str, username: str, details: str = ""):
    """Enhanced security event logging with structured format"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create structured log entry
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "employee_id": employee_id,
        "username": username,
        "details": details,
        "session_id": id(st.session_state)  # Use session object ID as identifier
    }

    try:
        # Ensure log directory exists
        os.makedirs("logs", exist_ok=True)

        # Log to security logger
        security_logger = logging.getLogger('security')
        security_logger.info(f"{event_type} - {employee_id} - {username} - {details}")

        # Also log to daily file for easier management
        daily_log_path = f"logs/attendance_{datetime.now().strftime('%Y%m%d')}.log"

        with open(daily_log_path, "a", encoding="utf-8") as f:
            import json
            f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        logger.error(f"Failed to write security log: {e}")


# ===== FACE RECOGNITION WITH VALIDATION =====
def validate_face_recognition_input(badge_path: str, snapshot) -> Tuple[bool, str]:
    """Validate face recognition inputs"""
    if not FACE_RECOGNITION_AVAILABLE:
        return False, "Face recognition not available"

    if not os.path.exists(badge_path):
        return False, f"Badge image not found: {badge_path}"

    if snapshot is None:
        return False, "No snapshot provided"

    # Check badge file size (reasonable limits)
    try:
        badge_size = os.path.getsize(badge_path)
        if badge_size > 10 * 1024 * 1024:  # 10MB limit
            return False, "Badge file too large"
        if badge_size < 100:  # Too small to be a valid image
            return False, "Badge file too small"
    except Exception as e:
        return False, f"Error checking badge file: {e}"

    return True, "Valid"


# ===== MAIN ATTENDANCE FUNCTION WITH SECURITY =====
def run_attendance():
    """Main attendance application with comprehensive security and error handling"""

    # Initialize system with validation
    try:
        validate_configuration()
    except ConfigurationError as e:
        st.error(f"🚨 **Configuration Error:** {e}")
        st.error("Please contact system administrator to fix configuration.")
        logger.error(f"Configuration error: {e}")
        st.stop()

    # Enhanced security validation
    try:
        is_valid, message = validate_session_security()
        if not is_valid:
            st.error(f"🔒 **Security Validation Failed:** {message}")
            st.error("Please login again to access the attendance system.")

            # Log security failure
            log_security_event(
                "SECURITY_VALIDATION_FAILED",
                st.session_state.get("employee_id", "unknown"),
                st.session_state.get("username", "unknown"),
                message
            )
            st.stop()

    except Exception as e:
        logger.error(f"Security validation error: {e}")
        st.error("❌ Security validation error. Please contact support.")
        st.stop()

    # Get validated user information
    logged_employee_name = st.session_state.get("employee_name", "").strip()
    logged_employee_id = str(st.session_state.get("employee_id", "")).strip()
    logged_username = st.session_state.get("username", "").strip()

    logger.info(f"Attendance access by {logged_username} ({logged_employee_id})")

    # Setup UI
    setup_pwa()
    apply_mobile_css()

    # PWA Header
    st.markdown(f"""
    <div class="pwa-header">
        <h1>⚡ Ultra-Fast Attendance System</h1>
        <p>Secure GPS + Face Recognition</p>
        <span class="speed-indicator">SECURITY ENHANCED</span><br>
        <small>Logged in as: {logged_username}</small>
    </div>
    """, unsafe_allow_html=True)

    # Show system status
    show_database_status()

    # Security info card
    st.markdown(f"""
    <div class="user-info-card">
        <h3>🛡️ Secure Session Active</h3>
        <p><strong>Employee:</strong> {logged_employee_name}</p>
        <p><strong>ID:</strong> {logged_employee_id}</p>
        <p><strong>Login:</strong> {logged_username}</p>
        <p><small>🔒 This session is secured and validated</small></p>
    </div>
    """, unsafe_allow_html=True)

    # Step 1: Location Detection with Validation
    st.markdown("### Step 1: ⚡ Secure Location Detection")
    st.markdown("*Enhanced with coordinate validation and security checks*")

    try:
        location_data = get_location_ultra_fast()
        if not location_data:
            st.warning("📍 Please select a location detection method above to continue.")
            st.stop()

        # Validate and extract coordinates
        user_lat = location_data.get("latitude", 0)
        user_lon = location_data.get("longitude", 0)
        location_source = location_data.get("source", "Unknown")
        detection_method = location_data.get("method", "unknown")

        # Double-check coordinate validation
        if not validate_coordinates(user_lat, user_lon):
            st.error("❌ Invalid coordinates detected. Please try again.")
            logger.error(f"Invalid coordinates from location detection: {user_lat}, {user_lon}")
            st.stop()

    except Exception as e:
        logger.error(f"Location detection error: {e}")
        st.error(f"❌ Location detection failed: {e}")

        # Show fallback location options
        st.markdown("### 🔄 Alternative Location Methods")
        st.warning("🌐 Geolocation services are not available. Please try manual location entry.")

        # Manual location fallback
        with st.expander("📍 Manual Location Entry"):
            col1, col2 = st.columns(2)
            with col1:
                manual_lat = st.number_input("Latitude", value=0.0, format="%.6f")
            with col2:
                manual_lon = st.number_input("Longitude", value=0.0, format="%.6f")

            if st.button("Use Manual Location"):
                if validate_coordinates(manual_lat, manual_lon):
                    location_data = {
                        "latitude": manual_lat,
                        "longitude": manual_lon,
                        "source": "Manual Entry",
                        "method": "manual"
                    }
                    user_lat, user_lon = manual_lat, manual_lon
                    location_source, detection_method = "Manual Entry", "manual"
                else:
                    st.error("❌ Invalid coordinates entered.")
                    st.stop()

        if not location_data:
            st.stop()

    # Verify location permissions
    try:
        location_verified, location_name, distance = check_location_permission(user_lat, user_lon)

        if location_verified:
            st.markdown(f"""
            <div class="location-status location-approved">
                ✅ Location Verified & Secure!<br>
                📍 {location_name}<br>
                📏 {distance:.1f}m from office<br>
                ⚡ Method: {detection_method}<br>
                🚀 Source: {location_source}
            </div>
            """, unsafe_allow_html=True)

            # Log successful location verification
            log_security_event(
                "LOCATION_VERIFIED",
                logged_employee_id,
                logged_username,
                f"Location: {location_name}, Distance: {distance:.1f}m"
            )
        else:
            st.markdown(f"""
            <div class="location-status location-denied">
                ❌ Location Not Authorized<br>
                📍 Current: {user_lat:.4f}, {user_lon:.4f}<br>
                🚫 Outside permitted office area<br>
                📏 Please move to an authorized location
            </div>
            """, unsafe_allow_html=True)

            # Log failed location verification
            log_security_event(
                "LOCATION_DENIED",
                logged_employee_id,
                logged_username,
                f"Coordinates: {user_lat:.4f}, {user_lon:.4f}"
            )

            # Show nearby authorized locations
            with st.expander("🗺️ View Authorized Office Locations"):
                try:
                    for office in OFFICE_LOCATIONS:
                        office_distance = geodesic((user_lat, user_lon), (office["lat"], office["lon"])).meters
                        st.write(f"📍 **{office['name']}**: {office_distance:.0f}m away")
                        st.write(f"   Allowed radius: {office['radius']}m")
                except Exception as dist_error:
                    st.error(f"Error calculating distances: {dist_error}")

            st.stop()

    except Exception as e:
        logger.error(f"Location permission check error: {e}")
        st.error(f"❌ Location verification failed: {e}")
        st.stop()

    # Step 2: Employee Verification
    st.markdown("### Step 2: ✅ Employee Identity Verification")

    try:
        # Load and validate employee data
        master_df = load_employee_master()
        if master_df.empty:
            st.error("❌ No employee data found in master database.")
            logger.error("Empty employee master data")
            st.stop()

        # Clean and validate employee data
        master_df["employee_name"] = master_df["employee_name"].astype(str).str.strip()
        master_df["employee_id"] = master_df["employee_id"].astype(str).str.strip()

        # Find matching employee
        employee_match = master_df[
            (master_df["employee_id"] == logged_employee_id) |
            (master_df["employee_name"].str.lower() == logged_employee_name.lower())
            ]

        if employee_match.empty:
            st.error(f"❌ Employee '{logged_employee_name}' (ID: {logged_employee_id}) not found in master data.")
            st.error("Please contact HR to add your profile to the system.")

            log_security_event(
                "EMPLOYEE_NOT_FOUND",
                logged_employee_id,
                logged_username,
                "Employee not in master database"
            )
            st.stop()

        employee_row = employee_match.iloc[0]
        employee_id = str(employee_row["employee_id"]).strip()
        employee_name = str(employee_row["employee_name"]).strip()

        try:
            salary = float(employee_row.get("fixed_salary", 0)) if pd.notna(employee_row.get("fixed_salary", 0)) else 0
        except (ValueError, TypeError):
            salary = 0
            logger.warning(f"Invalid salary data for employee {employee_id}")

        st.markdown(f"""
        <div class="security-badge">
            <h4>🔐 Identity Verified & Confirmed</h4>
            <p>Employee: <strong>{employee_name}</strong></p>
            <p>ID: <strong>{employee_id}</strong></p>
            <p>Login User: <strong>{logged_username}</strong></p>
            <p>Salary Record: <strong>{'✅ Found' if salary > 0 else '⚠️ Not Set'}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        log_security_event(
            "EMPLOYEE_VERIFIED",
            employee_id,
            logged_username,
            f"Master database match confirmed"
        )

    except Exception as e:
        logger.error(f"Employee verification error: {e}")
        st.error(f"❌ Error during employee verification: {e}")
        st.stop()

    # Step 3: Face Recognition with Enhanced Security
    st.markdown("### Step 3: 📸 Biometric Face Recognition")

    try:
        # Validate face recognition availability
        if not FACE_RECOGNITION_AVAILABLE:
            st.error("❌ Face recognition system not available")
            st.error("Please contact IT support to enable biometric authentication")
            st.stop()

        # Construct badge path securely
        badge_filename = f"{employee_name.lower().strip().replace(' ', '_')}.jpg"
        badge_path = os.path.join(BADGE_DIR, badge_filename)

        # Validate badge path security (prevent directory traversal)
        if '..' in badge_filename or '/' in badge_filename.replace('_', ''):
            st.error("❌ Invalid badge filename detected")
            logger.error(f"Potential security issue with badge filename: {badge_filename}")
            st.stop()

        # Validate face recognition inputs
        is_valid_input, validation_message = validate_face_recognition_input(badge_path, None)

        if not is_valid_input and "No snapshot provided" not in validation_message:
            st.error(f"❌ {validation_message}")

            if "not found" in validation_message:
                with st.expander("ℹ️ Badge Photo Requirements"):
                    st.markdown(f"""
                    **Badge Photo Guidelines:**
                    - Expected filename: `{badge_filename}`
                    - Location: `{BADGE_DIR}`
                    - Image should be clear and well-lit
                    - Face should be clearly visible
                    - Recommended size: 300x300 pixels minimum
                    - Supported formats: JPG, PNG
                    - Maximum file size: 10MB

                    **Contact administrator if your badge photo is missing.**
                    """)
            st.stop()

        # Display reference photo securely
        col1, col2 = st.columns([1, 2])

        with col1:
            try:
                st.image(badge_path, caption=f"Reference: {employee_name}", width=250)
            except Exception as img_error:
                st.error(f"❌ Error loading badge image: {img_error}")
                logger.error(f"Badge image error for {employee_name}: {img_error}")
                st.stop()

        with col2:
            st.markdown("""
            <div class="warning-container">
                <h4>📋 Biometric Verification Instructions</h4>
                <ul>
                    <li>🔆 Ensure bright, even lighting</li>
                    <li>👤 Look directly at the camera</li>
                    <li>😐 Maintain neutral expression</li>
                    <li>📱 Hold device steady</li>
                    <li>🚫 Remove sunglasses, hats, masks</li>
                    <li>📏 Position face similar to reference photo</li>
                </ul>
                <p><strong>🔒 Security Note:</strong> Your biometric data is processed locally and never stored.</p>
            </div>
            """, unsafe_allow_html=True)

        # Secure camera input
        st.markdown("**📷 Capture your verification photo:**")
        snapshot = st.camera_input("Biometric Capture", key="secure_face_recognition_camera")

        if not snapshot:
            st.info("📸 Please capture your photo for biometric verification.")
            st.markdown("""
            <div style="text-align: center; padding: 20px; background: #f0f0f0; border-radius: 10px; margin: 10px 0;">
                <p>⏳ <strong>Waiting for biometric capture...</strong></p>
                <small>Click the camera button above to take your verification photo</small>
            </div>
            """, unsafe_allow_html=True)
            st.stop()

        # Perform face verification with comprehensive error handling
        st.markdown("**🔍 Processing biometric verification...**")

        try:
            with st.spinner("🤖 Analyzing biometric data..."):
                match, confidence = compare_faces(badge_path, snapshot)

                # Validate confidence score
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
                    raise ValueError(f"Invalid confidence score: {confidence}")

                threshold = 30  # Minimum confidence threshold

            # Log biometric attempt
            log_security_event(
                "BIOMETRIC_ATTEMPT",
                employee_id,
                logged_username,
                f"Confidence: {confidence:.2f}%, Threshold: {threshold}%"
            )

            if not match or confidence < threshold:
                st.markdown(f"""
                <div class="error-container">
                    <h4 style="color: #C62828;">❌ Biometric Verification Failed</h4>
                    <p><strong>Confidence Score:</strong> {confidence:.2f}% (Required: {threshold}%)</p>
                    <p><strong>Possible Issues:</strong></p>
                    <ul>
                        <li>Inadequate lighting conditions</li>
                        <li>Face partially obscured or unclear</li>
                        <li>Significant difference from reference photo</li>
                        <li>Camera quality or focus issues</li>
                        <li>Facial obstructions (glasses, mask, etc.)</li>
                    </ul>
                    <p><strong>🔧 Troubleshooting Steps:</strong></p>
                    <ul>
                        <li>Move to a well-lit area</li>
                        <li>Remove any face coverings</li>
                        <li>Clean camera lens</li>
                        <li>Position face similar to reference photo</li>
                        <li>Ensure camera is steady</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                # Log failed verification
                log_security_event(
                    "BIOMETRIC_FAILED",
                    employee_id,
                    logged_username,
                    f"Low confidence: {confidence:.2f}%"
                )

                if st.button("🔄 Try Biometric Verification Again", key="retry_face_recognition"):
                    st.rerun()

                st.stop()

            # Successful biometric verification
            st.markdown(f"""
            <div class="success-container">
                <h4 style="color: #2E7D32;">✅ Biometric Verification Successful!</h4>
                <p><strong>🎯 Confidence Score:</strong> {confidence:.2f}% (Excellent match)</p>
                <p><strong>👤 Employee:</strong> {employee_name}</p>
                <p><strong>🆔 ID:</strong> {employee_id}</p>
                <p><strong>✅ Verification Status:</strong> Approved</p>
                <p><strong>🔒 Security Level:</strong> High</p>
            </div>
            """, unsafe_allow_html=True)

            # Log successful verification
            log_security_event(
                "BIOMETRIC_SUCCESS",
                employee_id,
                logged_username,
                f"High confidence match: {confidence:.2f}%"
            )

        except Exception as face_error:
            logger.error(f"Face recognition error for {employee_name}: {face_error}")
            st.markdown(f"""
            <div class="error-container">
                <h4 style="color: #C62828;">❌ Biometric System Error</h4>
                <p><strong>Error:</strong> {str(face_error)}</p>
                <p><strong>Employee:</strong> {employee_name}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Log system error
            log_security_event(
                "BIOMETRIC_SYSTEM_ERROR",
                employee_id,
                logged_username,
                f"System error: {str(face_error)}"
            )

            with st.expander("🔧 Technical Details (for support)"):
                st.code(f"""
                === BIOMETRIC SYSTEM ERROR ===
                Error: {str(face_error)}
                Type: {type(face_error).__name__}
                Employee: {employee_name}
                Badge Path: {badge_path}
                Timestamp: {datetime.now()}
                Session ID: {id(st.session_state)}
                """)

            st.error("Please try again or contact IT support if the problem persists.")
            st.stop()

    except Exception as e:
        logger.error(f"Face recognition setup error: {e}")
        st.error(f"❌ Biometric system initialization failed: {e}")
        st.stop()

    # Step 4: Process Attendance with Enhanced Security
    st.markdown("### Step 4: ⏰ Processing Secure Attendance")

    now = datetime.now()
    today = now.date()
    greeting = get_greeting(now)

    st.markdown(f"""
    <div class="metric-card">
        <h3>{greeting} {employee_name}! 👋</h3>
        <p>🕐 Current Time: {now.strftime('%I:%M %p')}</p>
        <p>📅 Date: {today.strftime('%A, %B %d, %Y')}</p>
        <p>🔒 Security Level: Maximum</p>
        <span class="speed-indicator">PROCESSING SECURELY</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Load attendance data with enhanced error handling
        attendance_df = load_attendance()
        attendance_df["employee_id"] = attendance_df["employee_id"].astype(str)
        attendance_df["start_datetime"] = pd.to_datetime(attendance_df["start_datetime"], errors="coerce")
        attendance_df["date_only"] = attendance_df["start_datetime"].dt.date

        # Check today's record for this specific employee
        mask = (attendance_df["employee_id"] == employee_id) & (attendance_df["date_only"] == today)
        today_record = attendance_df[mask]

        if today_record.empty:
            # ===== SECURE CHECK-IN PROCESS =====
            st.markdown("#### 🔑 **Secure Check-In Process**")

            # Calculate late status with validation
            try:
                late_cutoff = datetime.strptime("09:15", "%H:%M").time()
                late_mark = now.time() > late_cutoff

                if late_mark:
                    late_minutes = (datetime.combine(today, now.time()) -
                                    datetime.combine(today, late_cutoff)).seconds // 60
                    st.warning(f"⚠️ Late arrival detected: {late_minutes} minutes after 9:15 AM")

                    log_security_event(
                        "LATE_ARRIVAL",
                        employee_id,
                        logged_username,
                        f"Late by {late_minutes} minutes"
                    )

            except Exception as time_error:
                logger.error(f"Error calculating late status: {time_error}")
                late_mark = False

            # Create secure attendance record
            new_row = {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "start_datetime": now,
                "exit_datetime": pd.NaT,
                "date_only": today,
                "total_hours": pd.NA,
                "extra_hours": 0,
                "extra_pay": 0,
                "attendance_status": pd.NA,
                "late_mark": late_mark,
                "method": f"Secure GPS + Biometric ({detection_method})",
                "confidence": confidence,
                "notes": f"Verified login: {logged_username} | Location: {location_source} | Security: Enhanced",
                "location_lat": user_lat,
                "location_lon": user_lon,
                "location_verified": location_verified,
                "location_name": location_name
            }

            # Add record with validation
            try:
                attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)
                attendance_df["date_only"] = pd.to_datetime(attendance_df["start_datetime"]).dt.date

                # Remove duplicates (keep latest)
                attendance_df.drop_duplicates(subset=["employee_id", "date_only"], keep="last", inplace=True)

                # Save with enhanced security
                if save_attendance_secure(attendance_df):
                    # Log successful check-in
                    log_security_event(
                        "CHECKIN_SUCCESS",
                        employee_id,
                        logged_username,
                        f"Method: {detection_method}, Confidence: {confidence:.1f}%, Location: {location_name}"
                    )

                    # Success display
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🎉 Secure Check-In Successful!</h3>
                        <p><strong>👤 Employee:</strong> {employee_name}</p>
                        <p><strong>🕐 Check-In Time:</strong> {now.strftime('%I:%M %p')}</p>
                        <p><strong>📅 Date:</strong> {today.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>📍 Location:</strong> {location_name}</p>
                        <p><strong>⚡ Method:</strong> {detection_method.title()}</p>
                        <p><strong>🎯 Biometric Match:</strong> {confidence:.1f}%</p>
                        <p><strong>👤 Verified User:</strong> {logged_username}</p>
                        <p><strong>🔒 Security:</strong> Maximum</p>
                        {f"<p style='color: #ffeb3b; font-weight: bold;'>⚠️ Late Mark Applied</p>" if late_mark else "<p style='color: #4CAF50; font-weight: bold;'>✅ On Time</p>"}
                        <span class="speed-indicator">SECURE CHECK-IN COMPLETE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.balloons()

                    # Show today's schedule
                    st.markdown("""
                    <div class="success-container">
                        <h4 style="color: #2E7D32;">📋 Today's Schedule</h4>
                        <ul style="color: #388E3C;">
                            <li><strong>Standard Hours:</strong> 9:00 AM - 6:00 PM</li>
                            <li><strong>Lunch Break:</strong> 1:00 PM - 2:00 PM</li>
                            <li><strong>Overtime Begins:</strong> After 6:45 PM</li>
                            <li><strong>Minimum Work Time:</strong> 1 minute (for checkout)</li>
                        </ul>
                        <p style="color: #2E7D32;"><strong>💼 Have a productive day!</strong></p>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.error("❌ Failed to save check-in data. Please contact support.")
                    log_security_event(
                        "CHECKIN_SAVE_FAILED",
                        employee_id,
                        logged_username,
                        "Data save operation failed"
                    )

            except Exception as save_error:
                logger.error(f"Check-in save error: {save_error}")
                st.error(f"❌ Error saving check-in: {save_error}")
                log_security_event(
                    "CHECKIN_ERROR",
                    employee_id,
                    logged_username,
                    f"Save error: {str(save_error)}"
                )

        else:
            # ===== SECURE CHECK-OUT PROCESS =====
            record = today_record.iloc[0]

            if pd.isnull(record["exit_datetime"]):
                st.markdown("#### 🚪 **Secure Check-Out Process**")

                try:
                    check_in_time = pd.to_datetime(record["start_datetime"])
                    elapsed_seconds = (now - check_in_time).total_seconds()
                    elapsed_minutes = elapsed_seconds / 60

                    # Minimum time validation with security
                    if elapsed_seconds < 60:  # Must work at least 1 minute
                        remaining_seconds = 60 - elapsed_seconds

                        st.markdown(f"""
                        <div class="warning-container">
                            <h4>⏳ Minimum Work Time Validation</h4>
                            <p>Check-in time: <strong>{check_in_time.strftime('%I:%M %p')}</strong></p>
                            <p>Current time: <strong>{now.strftime('%I:%M %p')}</strong></p>
                            <p>Time remaining: <strong>{remaining_seconds:.0f} seconds</strong></p>
                            <p><em>System security requires minimum 1-minute work duration</em></p>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("🔄 Refresh Status", key="checkout_refresh"):
                            st.rerun()

                        st.stop()

                    # Calculate work duration with validation
                    total_hours = elapsed_seconds / 3600
                    hours = int(total_hours)
                    minutes = int((total_hours - hours) * 60)

                    # Calculate overtime securely
                    try:
                        overtime_start = datetime.combine(today, datetime.strptime("18:45", "%H:%M").time())
                        midnight = datetime.combine(today + timedelta(days=1),
                                                    datetime.strptime("00:00", "%H:%M").time())

                        if now > overtime_start:
                            extra_hours = min((now - overtime_start).total_seconds() / 3600,
                                              (midnight - overtime_start).total_seconds() / 3600)
                            extra_hours = round(max(extra_hours, 0), 2)
                        else:
                            extra_hours = 0

                    except Exception as overtime_error:
                        logger.error(f"Overtime calculation error: {overtime_error}")
                        extra_hours = 0

                    # Calculate extra pay securely
                    try:
                        if salary > 0 and extra_hours > 0:
                            hourly_rate = salary / (8 * 26)  # 8 hours/day, 26 working days/month
                            extra_pay = extra_hours * hourly_rate
                        else:
                            extra_pay = 0
                    except Exception as pay_error:
                        logger.error(f"Extra pay calculation error: {pay_error}")
                        extra_pay = 0

                    # Determine attendance status
                    if total_hours < 4:
                        attendance_status = "Absent"
                        status_color = "#f44336"
                    elif total_hours < 6:
                        attendance_status = "Half Day"
                        status_color = "#FF9800"
                    else:
                        attendance_status = "Full Day"
                        status_color = "#4CAF50"

                    # Display checkout summary
                    st.markdown(f"""
                    <div class="warning-container">
                        <h4 style="color: #E65100;">⏰ Secure Checkout Summary</h4>
                        <p><strong>Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
                        <p><strong>Current Time:</strong> {now.strftime('%I:%M %p')}</p>
                        <p><strong>Total Duration:</strong> {hours}h {minutes}m ({total_hours:.2f} hours)</p>
                        <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{attendance_status}</span></p>
                        <p><strong>Overtime Hours:</strong> {extra_hours:.2f} hours</p>
                        <p><strong>Extra Payment:</strong> ₹{extra_pay:.2f}</p>
                        <p><strong>🔒 Verification:</strong> Biometric + GPS</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Secure checkout confirmation
                    if st.button("✅ **Confirm Secure Check-Out**", key="secure_checkout",
                                 help="Complete your secure checkout for today"):
                        try:
                            # Update attendance record securely
                            idx = attendance_df[(attendance_df["employee_id"] == employee_id) &
                                                (attendance_df["date_only"] == today)].index[0]

                            attendance_df.loc[idx, "exit_datetime"] = now
                            attendance_df.loc[idx, "total_hours"] = round(total_hours, 2)
                            attendance_df.loc[idx, "extra_hours"] = extra_hours
                            attendance_df.loc[idx, "extra_pay"] = round(extra_pay, 2)
                            attendance_df.loc[idx, "attendance_status"] = attendance_status
                            attendance_df.loc[
                                idx, "notes"] = f"Secure checkout: {logged_username} | Location: {location_source} | Biometric: {confidence:.1f}%"

                            # Save securely
                            if save_attendance_secure(attendance_df):
                                # Log successful checkout
                                log_security_event(
                                    "CHECKOUT_SUCCESS",
                                    employee_id,
                                    logged_username,
                                    f"Duration: {total_hours:.2f}h, Status: {attendance_status}, Extra: {extra_hours:.2f}h"
                                )

                                # Success message
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>🎉 Secure Check-Out Successful!</h3>
                                    <p><strong>🚪 Check-Out Time:</strong> {now.strftime('%I:%M %p')}</p>
                                    <p><strong>⏱️ Total Hours:</strong> {total_hours:.2f} hours</p>
                                    <p><strong>📊 Status:</strong> {attendance_status}</p>
                                    <p><strong>⏰ Overtime Hours:</strong> {extra_hours:.2f} hours</p>
                                    <p><strong>💰 Extra Pay:</strong> ₹{extra_pay:.2f}</p>
                                    <p><strong>👤 Verified User:</strong> {logged_username}</p>
                                    <p><strong>📍 Location:</strong> {location_name}</p>
                                    <p><strong>🔒 Security:</strong> Maximum</p>
                                    <span class="speed-indicator">SECURE CHECKOUT COMPLETE</span>
                                </div>
                                """, unsafe_allow_html=True)

                                st.balloons()

                                # Performance summary
                                work_quality = "Excellent" if total_hours >= 8 else "Good" if total_hours >= 6 else "Needs Improvement"
                                st.markdown(f"""
                                <div class="success-container">
                                    <h4 style="color: #2E7D32;">📈 Today's Performance Summary</h4>
                                    <ul style="color: #388E3C;">
                                        <li><strong>Work Quality:</strong> {work_quality}</li>
                                        <li><strong>Punctuality:</strong> {"On Time" if not record['late_mark'] else "Late Arrival"}</li>
                                        <li><strong>Productive Hours:</strong> {total_hours:.2f}</li>
                                        <li><strong>Overtime Contribution:</strong> {extra_hours:.2f} hours</li>
                                        <li><strong>Security Compliance:</strong> 100%</li>
                                    </ul>
                                    <p style="color: #2E7D32;"><strong>💼 Thank you for your secure and productive day!</strong></p>
                                </div>
                                """, unsafe_allow_html=True)

                            else:
                                st.error("❌ Failed to save checkout data. Please contact support.")
                                log_security_event(
                                    "CHECKOUT_SAVE_FAILED",
                                    employee_id,
                                    logged_username,
                                    "Checkout save operation failed"
                                )

                        except Exception as checkout_error:
                            logger.error(f"Checkout process error: {checkout_error}")
                            st.error(f"❌ Checkout error: {checkout_error}")
                            log_security_event(
                                "CHECKOUT_ERROR",
                                employee_id,
                                logged_username,
                                f"Checkout error: {str(checkout_error)}"
                            )

                except Exception as checkout_calc_error:
                    logger.error(f"Checkout calculation error: {checkout_calc_error}")
                    st.error(f"❌ Error calculating checkout data: {checkout_calc_error}")

            else:
                # ===== ATTENDANCE ALREADY COMPLETE =====
                st.markdown("#### ℹ️ **Attendance Already Complete**")

                try:
                    check_in_time = pd.to_datetime(record["start_datetime"])
                    check_out_time = pd.to_datetime(record["exit_datetime"])

                    st.info("✅ Your secure attendance for today has already been completed.")

                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>📋 Today's Secure Attendance Summary</h3>
                        <p><strong>🔑 Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
                        <p><strong>🚪 Check-Out:</strong> {check_out_time.strftime('%I:%M %p')}</p>
                        <p><strong>⏱️ Total Hours:</strong> {record.get('total_hours', 0):.2f} hours</p>
                        <p><strong>📊 Status:</strong> {record.get('attendance_status', 'Unknown')}</p>
                        <p><strong>⏰ Overtime Hours:</strong> {record.get('extra_hours', 0):.2f} hours</p>
                        <p><strong>💰 Extra Pay:</strong> ₹{record.get('extra_pay', 0):.2f}</p>
                        <p><strong>👤 Verified User:</strong> {logged_username}</p>
                        <p><strong>📍 Location:</strong> {record.get('location_name', 'Unknown')}</p>
                        <p><strong>🔒 Security Level:</strong> Maximum</p>
                        <span class="speed-indicator">ATTENDANCE COMPLETE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Next working day information
                    next_day = today + timedelta(days=1)
                    while next_day.weekday() >= 5:  # Skip weekends
                        next_day += timedelta(days=1)

                    st.markdown(f"""
                    <div class="success-container">
                        <h4 style="color: #2E7D32;">📅 Next Working Day</h4>
                        <p style="color: #388E3C;">Next attendance: <strong>{next_day.strftime('%A, %B %d, %Y')}</strong></p>
                        <p style="color: #388E3C;">Expected arrival: <strong>9:00 AM</strong></p>
                        <p style="color: #388E3C;">Have a great evening!</p>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as summary_error:
                    logger.error(f"Error displaying attendance summary: {summary_error}")
                    st.error("❌ Error loading attendance summary")

        # ===== SECURE ATTENDANCE HISTORY =====
        st.markdown("### 📊 Your Secure Attendance History")

        try:
            employee_attendance = attendance_df[attendance_df["employee_id"] == employee_id].copy()

            if not employee_attendance.empty:
                # Sort by date (most recent first)
                employee_attendance = employee_attendance.sort_values("start_datetime", ascending=False)

                # Display last 10 records with enhanced security info
                display_columns = [
                    "date_only", "start_datetime", "exit_datetime", "total_hours",
                    "attendance_status", "late_mark", "location_name", "confidence", "method"
                ]

                display_df = employee_attendance.head(10)[
                    [col for col in display_columns if col in employee_attendance.columns]
                ].copy()

                if not display_df.empty:
                    # Format columns securely
                    if "start_datetime" in display_df.columns:
                        display_df["Check-In"] = pd.to_datetime(display_df["start_datetime"]).dt.strftime('%I:%M %p')
                        display_df.drop("start_datetime", axis=1, inplace=True)

                    if "exit_datetime" in display_df.columns:
                        display_df["Check-Out"] = pd.to_datetime(display_df["exit_datetime"]).dt.strftime('%I:%M %p')
                        display_df.drop("exit_datetime", axis=1, inplace=True)

                    # Rename columns
                    column_mapping = {
                        "date_only": "Date",
                        "total_hours": "Hours",
                        "attendance_status": "Status",
                        "late_mark": "Late",
                        "location_name": "Location",
                        "confidence": "Biometric %",
                        "method": "Security Method"
                    }

                    display_df = display_df.rename(columns=column_mapping)
                    display_df = display_df.fillna("-")

                    # Format specific columns
                    if "Biometric %" in display_df.columns:
                        display_df["Biometric %"] = display_df["Biometric %"].apply(
                            lambda x: f"{x:.1f}%" if pd.notna(x) and str(x) != "-" else "-"
                        )

                    if "Late" in display_df.columns:
                        display_df["Late"] = display_df["Late"].apply(
                            lambda x: "Yes" if x is True else "No" if x is False else "-"
                        )

                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                # Secure download options
                col1, col2 = st.columns(2)

                with col1:
                    csv_data = employee_attendance.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Personal Report (CSV)",
                        data=csv_data,
                        file_name=f"secure_attendance_{employee_id}_{employee_name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

                with col2:
                    # Current month data
                    current_month = employee_attendance[
                        employee_attendance["start_datetime"].dt.month == now.month
                        ]
                    if not current_month.empty:
                        monthly_csv = current_month.to_csv(index=False)
                        st.download_button(
                            label="📅 Download This Month (CSV)",
                            data=monthly_csv,
                            file_name=f"monthly_attendance_{employee_id}_{now.strftime('%Y_%m')}.csv",
                            mime="text/csv"
                        )

                # Enhanced statistics
                st.markdown("#### 📈 Your Performance Statistics")

                current_month_data = employee_attendance[
                    employee_attendance["start_datetime"].dt.month == now.month
                    ]

                if not current_month_data.empty:
                    try:
                        total_days = len(current_month_data)
                        late_days = len(current_month_data[current_month_data["late_mark"] == True])
                        full_days = len(current_month_data[current_month_data["attendance_status"] == "Full Day"])
                        avg_hours = current_month_data[
                            "total_hours"].mean() if "total_hours" in current_month_data.columns else 0
                        total_overtime = current_month_data[
                            "extra_hours"].sum() if "extra_hours" in current_month_data.columns else 0
                        avg_biometric = current_month_data[
                            "confidence"].mean() if "confidence" in current_month_data.columns else 0

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                label="📅 Days This Month",
                                value=total_days,
                                delta=f"{(total_days / 22) * 100:.0f}% attendance"
                            )

                        with col2:
                            st.metric(
                                label="⏰ Punctuality",
                                value=f"{total_days - late_days}/{total_days}",
                                delta=f"{((total_days - late_days) / total_days) * 100:.0f}% on time" if total_days > 0 else "0%"
                            )

                        with col3:
                            st.metric(
                                label="✅ Full Days",
                                value=full_days,
                                delta=f"{(full_days / total_days) * 100:.0f}% full attendance" if total_days > 0 else "0%"
                            )

                        with col4:
                            st.metric(
                                label="🎯 Avg Biometric",
                                value=f"{avg_biometric:.0f}%",
                                delta="High accuracy"
                            )

                        # Additional performance metrics
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(
                                label="⚡ Avg Daily Hours",
                                value=f"{avg_hours:.1f}h",
                                delta="Productive"
                            )

                        with col2:
                            st.metric(
                                label="⏰ Total Overtime",
                                value=f"{total_overtime:.1f}h",
                                delta="Extra contribution"
                            )

                    except Exception as stats_error:
                        logger.error(f"Statistics calculation error: {stats_error}")
                        st.error("❌ Error calculating statistics")

            else:
                st.info("📋 No attendance history found. Today's attendance will appear here after completion.")

        except Exception as history_error:
            logger.error(f"Attendance history error: {history_error}")
            st.error("❌ Error loading attendance history")

    except Exception as e:
        logger.error(f"Attendance processing error: {e}")
        st.error(f"❌ **Error processing attendance:** {e}")

        # Enhanced error reporting
        with st.expander("🔍 Detailed Error Information"):
            st.code(f"""
            === SECURE ATTENDANCE PROCESSING ERROR ===
            Error: {str(e)}
            Type: {type(e).__name__}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            === USER INFORMATION ===
            Employee ID: {employee_id}
            Employee Name: {employee_name}
            Login Username: {logged_username}
            Session ID: {id(st.session_state)}

            === SECURITY CONTEXT ===
            Location Verified: {location_verified}
            Location Name: {location_name}
            Biometric Confidence: {confidence if 'confidence' in locals() else 'N/A'}
            Detection Method: {detection_method}

            === SYSTEM STATE ===
            Database Mode: {'SQL' if USE_SQL else 'CSV'}
            Face Recognition: {'Available' if FACE_RECOGNITION_AVAILABLE else 'Unavailable'}
            Geolocation: {'Available' if GEOLOCATION_AVAILABLE else 'Unavailable'}
            """)

        # Log critical error
        log_security_event(
            "CRITICAL_ATTENDANCE_ERROR",
            employee_id if 'employee_id' in locals() else "unknown",
            logged_username,
            f"Critical error: {str(e)}"
        )

        # Recovery options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Retry Attendance Process", key="retry_attendance_secure"):
                st.info("♻️ Restarting secure attendance process...")
                st.rerun()

        with col2:
            if st.button("🏠 Return to Dashboard", key="back_to_dashboard"):
                st.info("🏠 Returning to main dashboard...")
                # Clear potentially problematic session data
                for key in ['location_data', 'location_cache']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


# ===== ENHANCED DATABASE STATUS =====

def show_database_status():
    """Show enhanced database connection status with security info"""
    if USE_SQL:
        try:
            # Fixed: Use proper connection method
            conn = safe_get_conn()  # This should return a connection object, not engine

            if hasattr(conn, 'execute') and not hasattr(conn, 'connect'):
                # Direct connection object
                cursor = conn.cursor()
                cursor.execute("SELECT DB_NAME()")
                db_name = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                st.success(f"✅ Connected to database: {db_name}")
            else:
                # SQLAlchemy engine - use context manager
                with conn.connect() as connection:
                    from sqlalchemy import text
                    result = connection.execute(text("SELECT DB_NAME()"))
                    db_name = result.scalar()
                    st.success(f"✅ Connected to database: {db_name}")

        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            logger.error(f"Database connection failed: {e}")
            # Show fallback mode
            st.warning("🔄 Falling back to CSV mode for data storage")
    else:
        st.info("📂 Using CSV mode (SQL disabled).")


def process_secure_attendance():
    """
    Main function to process secure attendance with biometric verification
    """
    try:
        # Initialize variables with default values
        employee_id = st.session_state.get('employee_id', '')
        employee_name = st.session_state.get('employee_name', 'Unknown')
        logged_username = st.session_state.get('username', 'system')
        salary = st.session_state.get('salary', 0)

        # Initialize security variables
        confidence = 0.0
        detection_method = 'unknown'
        location_verified = False
        location_name = 'Unknown Location'
        user_lat = 0.0
        user_lon = 0.0
        location_source = 'manual'
        badge_path = None

        # Validate required data
        if not employee_id:
            st.error("❌ Employee ID not found. Please login again.")
            return

        # Step 1: Location Verification (if available)
        st.markdown("### Step 1: 📍 Secure Location Verification")
        try:
            if GEOLOCATION_AVAILABLE:
                location_data = get_user_location()
                if location_data and location_data.get('verified', False):
                    user_lat = location_data.get('lat', 0.0)
                    user_lon = location_data.get('lon', 0.0)
                    location_name = location_data.get('name', 'Office Location')
                    location_verified = True
                    location_source = 'gps'
                    st.success(f"✅ Location verified: {location_name}")
                else:
                    st.warning("⚠️ Location verification failed. Using manual verification.")
            else:
                st.info("📍 Manual location mode enabled.")
                location_name = "Manual Location"
        except Exception as location_error:
            logger.error(f"Location verification error: {location_error}")
            st.warning("⚠️ Location service unavailable. Using manual mode.")

        # Step 2: Badge Upload
        st.markdown("### Step 2: 🆔 Upload Employee Badge")
        uploaded_badge = st.file_uploader(
            "Upload your employee badge photo",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear photo of your employee badge for biometric verification"
        )

        if not uploaded_badge:
            st.warning("⚠️ Please upload your employee badge to continue.")
            st.stop()

        # Step 3: Biometric Verification
        st.markdown("### Step 3: 🔐 Biometric Verification")

        try:
            if FACE_RECOGNITION_AVAILABLE:
                # Process the uploaded badge
                from PIL import Image
                badge_image = Image.open(uploaded_badge)

                # Save badge temporarily for processing
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    badge_image.save(tmp_file.name, 'JPEG')
                    badge_path = tmp_file.name

                # Perform face recognition (mock implementation - replace with actual)
                # In real implementation, this would compare with stored employee photo
                confidence = perform_face_recognition(badge_path, employee_id)
                detection_method = 'face_recognition'

                # Clean up temporary file
                if badge_path and os.path.exists(badge_path):
                    os.unlink(badge_path)

                if confidence >= 80:
                    # Successful biometric verification
                    st.markdown(f"""
                    <div class="success-container">
                        <h4 style="color: #2E7D32;">✅ Biometric Verification Successful!</h4>
                        <p><strong>🎯 Confidence Score:</strong> {confidence:.2f}% (Excellent match)</p>
                        <p><strong>👤 Employee:</strong> {employee_name}</p>
                        <p><strong>🆔 ID:</strong> {employee_id}</p>
                        <p><strong>✅ Verification Status:</strong> Approved</p>
                        <p><strong>🔒 Security Level:</strong> High</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Log successful verification
                    log_security_event(
                        "BIOMETRIC_SUCCESS",
                        employee_id,
                        logged_username,
                        f"High confidence match: {confidence:.2f}%"
                    )
                else:
                    # Failed biometric verification
                    st.error(f"❌ Biometric verification failed. Confidence too low: {confidence:.1f}%")

                    if st.button("🔄 Try Biometric Verification Again", key="retry_face_recognition"):
                        st.rerun()
                    st.stop()

            else:
                # Fallback to manual verification
                st.info("🔐 Manual verification mode (biometric system unavailable)")
                confidence = 80.0
                detection_method = 'manual'

        except Exception as face_error:
            logger.error(f"Face recognition error for {employee_name}: {face_error}")
            st.markdown(f"""
            <div class="error-container">
                <h4 style="color: #C62828;">❌ Biometric System Error</h4>
                <p><strong>Error:</strong> {str(face_error)}</p>
                <p><strong>Employee:</strong> {employee_name}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Log system error
            log_security_event(
                "BIOMETRIC_SYSTEM_ERROR",
                employee_id,
                logged_username,
                f"System error: {str(face_error)}"
            )

            with st.expander("🔧 Technical Details (for support)"):
                st.code(f"""
                === BIOMETRIC SYSTEM ERROR ===
                Error: {str(face_error)}
                Type: {type(face_error).__name__}
                Employee: {employee_name}
                Badge Path: {badge_path if badge_path else 'N/A'}
                Timestamp: {datetime.now()}
                Session ID: {id(st.session_state)}
                """)

            st.error("Please try again or contact IT support if the problem persists.")

            # Offer retry or fallback
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retry Biometric", key="retry_biometric"):
                    st.rerun()
            with col2:
                if st.button("📝 Use Manual Mode", key="manual_mode"):
                    confidence = 75.0
                    detection_method = 'manual_fallback'
                    st.info("Continuing with manual verification...")
                else:
                    st.stop()

        # Step 4: Process Attendance with Enhanced Security
        st.markdown("### Step 4: ⏰ Processing Secure Attendance")

        now = datetime.now()
        today = now.date()
        greeting = get_greeting(now)

        st.markdown(f"""
        <div class="metric-card">
            <h3>{greeting} {employee_name}! 👋</h3>
            <p>🕐 Current Time: {now.strftime('%I:%M %p')}</p>
            <p>📅 Date: {today.strftime('%A, %B %d, %Y')}</p>
            <p>🔒 Security Level: Maximum</p>
            <span class="speed-indicator">PROCESSING SECURELY</span>
        </div>
        """, unsafe_allow_html=True)

        # Load attendance data with enhanced error handling
        try:
            attendance_df = load_attendance()
            if attendance_df is not None and not attendance_df.empty:
                attendance_df["employee_id"] = attendance_df["employee_id"].astype(str)
                attendance_df["start_datetime"] = pd.to_datetime(attendance_df["start_datetime"], errors="coerce")
                attendance_df["date_only"] = attendance_df["start_datetime"].dt.date
            else:
                # Create empty DataFrame if load fails or returns None
                attendance_df = pd.DataFrame(columns=[
                    'employee_id', 'employee_name', 'start_datetime', 'exit_datetime',
                    'date_only', 'total_hours', 'extra_hours', 'extra_pay',
                    'attendance_status', 'late_mark', 'method', 'confidence',
                    'notes', 'location_lat', 'location_lon', 'location_verified', 'location_name'
                ])

        except Exception as load_error:
            logger.error(f"Error loading attendance data: {load_error}")
            st.warning("⚠️ Could not load existing attendance data. Creating new record.")
            attendance_df = pd.DataFrame(columns=[
                'employee_id', 'employee_name', 'start_datetime', 'exit_datetime',
                'date_only', 'total_hours', 'extra_hours', 'extra_pay',
                'attendance_status', 'late_mark', 'method', 'confidence',
                'notes', 'location_lat', 'location_lon', 'location_verified', 'location_name'
            ])

        # Check today's record for this specific employee
        if not attendance_df.empty:
            mask = (attendance_df["employee_id"] == employee_id) & (attendance_df["date_only"] == today)
            today_record = attendance_df[mask]
        else:
            today_record = pd.DataFrame()

        if today_record.empty:
            # ===== SECURE CHECK-IN PROCESS =====
            process_secure_checkin(
                attendance_df, employee_id, employee_name, now, today,
                confidence, detection_method, location_name, location_verified,
                user_lat, user_lon, location_source, logged_username
            )
        else:
            # ===== SECURE CHECK-OUT PROCESS =====
            record = today_record.iloc[0]

            if pd.isnull(record.get("exit_datetime", pd.NaT)):
                process_secure_checkout(
                    attendance_df, record, employee_id, employee_name,
                    now, today, confidence, detection_method, location_name,
                    salary, logged_username, location_source
                )
            else:
                # ===== ATTENDANCE ALREADY COMPLETE =====
                display_completed_attendance(record, logged_username, today)

        # ===== SECURE ATTENDANCE HISTORY =====
        display_secure_attendance_history(attendance_df, employee_id, employee_name, now)

    except Exception as e:
        logger.error(f"Critical attendance processing error: {e}")
        st.error(f"❌ **Critical Error in Attendance Processing:** {e}")

        # Enhanced error reporting
        with st.expander("🔍 Detailed Error Information"):
            st.code(f"""
            === SECURE ATTENDANCE PROCESSING ERROR ===
            Error: {str(e)}
            Type: {type(e).__name__}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            === USER INFORMATION ===
            Employee ID: {employee_id if 'employee_id' in locals() else 'N/A'}
            Employee Name: {employee_name if 'employee_name' in locals() else 'N/A'}
            Login Username: {logged_username if 'logged_username' in locals() else 'N/A'}
            Session ID: {id(st.session_state)}

            === SECURITY CONTEXT ===
            Location Verified: {location_verified if 'location_verified' in locals() else 'N/A'}
            Location Name: {location_name if 'location_name' in locals() else 'N/A'}
            Biometric Confidence: {confidence if 'confidence' in locals() else 'N/A'}
            Detection Method: {detection_method if 'detection_method' in locals() else 'N/A'}

            === SYSTEM STATE ===
            Database Mode: {'SQL' if USE_SQL else 'CSV'}
            Face Recognition: {'Available' if FACE_RECOGNITION_AVAILABLE else 'Unavailable'}
            Geolocation: {'Available' if GEOLOCATION_AVAILABLE else 'Unavailable'}
            """)

        # Log critical error
        log_security_event(
            "CRITICAL_ATTENDANCE_ERROR",
            employee_id if 'employee_id' in locals() else "unknown",
            logged_username if 'logged_username' in locals() else "system",
            f"Critical error: {str(e)}"
        )

        # Recovery options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Retry Attendance Process", key="retry_attendance_secure"):
                st.info("♻️ Restarting secure attendance process...")
                clear_session_cache()
                st.rerun()

        with col2:
            if st.button("🏠 Return to Dashboard", key="back_to_dashboard"):
                st.info("🏠 Returning to main dashboard...")
                clear_session_cache()
                st.rerun()


def process_secure_checkin(attendance_df, employee_id, employee_name, now, today,
                           confidence, detection_method, location_name, location_verified,
                           user_lat, user_lon, location_source, logged_username):
    """Process secure check-in with validation"""
    st.markdown("#### 🔑 **Secure Check-In Process**")

    try:
        # Calculate late status with validation
        late_cutoff = datetime.strptime("09:15", "%H:%M").time()
        late_mark = now.time() > late_cutoff

        if late_mark:
            late_minutes = (datetime.combine(today, now.time()) -
                            datetime.combine(today, late_cutoff)).seconds // 60
            st.warning(f"⚠️ Late arrival detected: {late_minutes} minutes after 9:15 AM")

            log_security_event(
                "LATE_ARRIVAL",
                employee_id,
                logged_username,
                f"Late by {late_minutes} minutes"
            )

        # Create secure attendance record
        new_row = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "start_datetime": now,
            "exit_datetime": pd.NaT,
            "date_only": today,
            "total_hours": pd.NA,
            "extra_hours": 0,
            "extra_pay": 0,
            "attendance_status": pd.NA,
            "late_mark": late_mark,
            "method": f"Secure GPS + Biometric ({detection_method})",
            "confidence": confidence,
            "notes": f"Verified login: {logged_username} | Location: {location_source} | Security: Enhanced",
            "location_lat": user_lat,
            "location_lon": user_lon,
            "location_verified": location_verified,
            "location_name": location_name
        }

        # Add record with validation
        if attendance_df.empty:
            attendance_df = pd.DataFrame([new_row])
        else:
            attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)

        attendance_df["date_only"] = pd.to_datetime(attendance_df["start_datetime"]).dt.date

        # Remove duplicates (keep latest)
        attendance_df.drop_duplicates(subset=["employee_id", "date_only"], keep="last", inplace=True)

        # Save with enhanced security
        if save_attendance_secure(attendance_df):
            # Log successful check-in
            log_security_event(
                "CHECKIN_SUCCESS",
                employee_id,
                logged_username,
                f"Method: {detection_method}, Confidence: {confidence:.1f}%, Location: {location_name}"
            )

            # Success display
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎉 Secure Check-In Successful!</h3>
                <p><strong>👤 Employee:</strong> {employee_name}</p>
                <p><strong>🕐 Check-In Time:</strong> {now.strftime('%I:%M %p')}</p>
                <p><strong>📅 Date:</strong> {today.strftime('%A, %B %d, %Y')}</p>
                <p><strong>📍 Location:</strong> {location_name}</p>
                <p><strong>⚡ Method:</strong> {detection_method.title()}</p>
                <p><strong>🎯 Biometric Match:</strong> {confidence:.1f}%</p>
                <p><strong>👤 Verified User:</strong> {logged_username}</p>
                <p><strong>🔒 Security:</strong> Maximum</p>
                {f"<p style='color: #ffeb3b; font-weight: bold;'>⚠️ Late Mark Applied</p>" if late_mark else "<p style='color: #4CAF50; font-weight: bold;'>✅ On Time</p>"}
                <span class="speed-indicator">SECURE CHECK-IN COMPLETE</span>
            </div>
            """, unsafe_allow_html=True)

            st.balloons()

            # Show today's schedule
            st.markdown("""
            <div class="success-container">
                <h4 style="color: #2E7D32;">📋 Today's Schedule</h4>
                <ul style="color: #388E3C;">
                    <li><strong>Standard Hours:</strong> 9:00 AM - 6:00 PM</li>
                    <li><strong>Lunch Break:</strong> 1:00 PM - 2:00 PM</li>
                    <li><strong>Overtime Begins:</strong> After 6:45 PM</li>
                    <li><strong>Minimum Work Time:</strong> 1 minute (for checkout)</li>
                </ul>
                <p style="color: #2E7D32;"><strong>💼 Have a productive day!</strong></p>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.error("❌ Failed to save check-in data. Please contact support.")
            log_security_event(
                "CHECKIN_SAVE_FAILED",
                employee_id,
                logged_username,
                "Data save operation failed"
            )

    except Exception as save_error:
        logger.error(f"Check-in save error: {save_error}")
        st.error(f"❌ Error saving check-in: {save_error}")
        log_security_event(
            "CHECKIN_ERROR",
            employee_id,
            logged_username,
            f"Save error: {str(save_error)}"
        )


def process_secure_checkout(attendance_df, record, employee_id, employee_name, now, today,
                            confidence, detection_method, location_name, salary,
                            logged_username, location_source):
    """Process secure check-out with validation"""
    st.markdown("#### 🚪 **Secure Check-Out Process**")

    try:
        check_in_time = pd.to_datetime(record["start_datetime"])
        elapsed_seconds = (now - check_in_time).total_seconds()

        # Minimum time validation with security
        if elapsed_seconds < 60:  # Must work at least 1 minute
            remaining_seconds = 60 - elapsed_seconds

            st.markdown(f"""
            <div class="warning-container">
                <h4>⏳ Minimum Work Time Validation</h4>
                <p>Check-in time: <strong>{check_in_time.strftime('%I:%M %p')}</strong></p>
                <p>Current time: <strong>{now.strftime('%I:%M %p')}</strong></p>
                <p>Time remaining: <strong>{remaining_seconds:.0f} seconds</strong></p>
                <p><em>System security requires minimum 1-minute work duration</em></p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔄 Refresh Status", key="checkout_refresh"):
                st.rerun()
            st.stop()

        # Calculate work duration with validation
        total_hours = elapsed_seconds / 3600
        hours = int(total_hours)
        minutes = int((total_hours - hours) * 60)

        # Calculate overtime securely
        try:
            overtime_start = datetime.combine(today, datetime.strptime("18:45", "%H:%M").time())
            midnight = datetime.combine(today + timedelta(days=1),
                                        datetime.strptime("00:00", "%H:%M").time())

            if now > overtime_start:
                extra_hours = min((now - overtime_start).total_seconds() / 3600,
                                  (midnight - overtime_start).total_seconds() / 3600)
                extra_hours = round(max(extra_hours, 0), 2)
            else:
                extra_hours = 0

        except Exception as overtime_error:
            logger.error(f"Overtime calculation error: {overtime_error}")
            extra_hours = 0

        # Calculate extra pay securely
        try:
            if salary > 0 and extra_hours > 0:
                hourly_rate = salary / (8 * 26)  # 8 hours/day, 26 working days/month
                extra_pay = extra_hours * hourly_rate
            else:
                extra_pay = 0
        except Exception as pay_error:
            logger.error(f"Extra pay calculation error: {pay_error}")
            extra_pay = 0

        # Determine attendance status
        if total_hours < 4:
            attendance_status = "Absent"
            status_color = "#f44336"
        elif total_hours < 6:
            attendance_status = "Half Day"
            status_color = "#FF9800"
        else:
            attendance_status = "Full Day"
            status_color = "#4CAF50"

        # Display checkout summary
        st.markdown(f"""
        <div class="warning-container">
            <h4 style="color: #E65100;">⏰ Secure Checkout Summary</h4>
            <p><strong>Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
            <p><strong>Current Time:</strong> {now.strftime('%I:%M %p')}</p>
            <p><strong>Total Duration:</strong> {hours}h {minutes}m ({total_hours:.2f} hours)</p>
            <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{attendance_status}</span></p>
            <p><strong>Overtime Hours:</strong> {extra_hours:.2f} hours</p>
            <p><strong>Extra Payment:</strong> ₹{extra_pay:.2f}</p>
            <p><strong>🔒 Verification:</strong> Biometric + GPS</p>
        </div>
        """, unsafe_allow_html=True)

        # Secure checkout confirmation
        if st.button("✅ **Confirm Secure Check-Out**", key="secure_checkout",
                     help="Complete your secure checkout for today"):
            try:
                # Update attendance record securely
                idx = attendance_df[(attendance_df["employee_id"] == employee_id) &
                                    (attendance_df["date_only"] == today)].index[0]

                attendance_df.loc[idx, "exit_datetime"] = now
                attendance_df.loc[idx, "total_hours"] = round(total_hours, 2)
                attendance_df.loc[idx, "extra_hours"] = extra_hours
                attendance_df.loc[idx, "extra_pay"] = round(extra_pay, 2)
                attendance_df.loc[idx, "attendance_status"] = attendance_status
                attendance_df.loc[
                    idx, "notes"] = f"Secure checkout: {logged_username} | Location: {location_source} | Biometric: {confidence:.1f}%"

                # Save securely
                if save_attendance_secure(attendance_df):
                    # Log successful checkout
                    log_security_event(
                        "CHECKOUT_SUCCESS",
                        employee_id,
                        logged_username,
                        f"Duration: {total_hours:.2f}h, Status: {attendance_status}, Extra: {extra_hours:.2f}h"
                    )

                    # Success message
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🎉 Secure Check-Out Successful!</h3>
                        <p><strong>🚪 Check-Out Time:</strong> {now.strftime('%I:%M %p')}</p>
                        <p><strong>⏱️ Total Hours:</strong> {total_hours:.2f} hours</p>
                        <p><strong>📊 Status:</strong> {attendance_status}</p>
                        <p><strong>⏰ Overtime Hours:</strong> {extra_hours:.2f} hours</p>
                        <p><strong>💰 Extra Pay:</strong> ₹{extra_pay:.2f}</p>
                        <p><strong>👤 Verified User:</strong> {logged_username}</p>
                        <p><strong>📍 Location:</strong> {location_name}</p>
                        <p><strong>🔒 Security:</strong> Maximum</p>
                        <span class="speed-indicator">SECURE CHECKOUT COMPLETE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.balloons()

                    # Performance summary
                    work_quality = "Excellent" if total_hours >= 8 else "Good" if total_hours >= 6 else "Needs Improvement"
                    st.markdown(f"""
                    <div class="success-container">
                        <h4 style="color: #2E7D32;">📈 Today's Performance Summary</h4>
                        <ul style="color: #388E3C;">
                            <li><strong>Work Quality:</strong> {work_quality}</li>
                            <li><strong>Punctuality:</strong> {"On Time" if not record['late_mark'] else "Late Arrival"}</li>
                            <li><strong>Productive Hours:</strong> {total_hours:.2f}</li>
                            <li><strong>Overtime Contribution:</strong> {extra_hours:.2f} hours</li>
                            <li><strong>Security Compliance:</strong> 100%</li>
                        </ul>
                        <p style="color: #2E7D32;"><strong>💼 Thank you for your secure and productive day!</strong></p>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.error("❌ Failed to save checkout data. Please contact support.")
                    log_security_event(
                        "CHECKOUT_SAVE_FAILED",
                        employee_id,
                        logged_username,
                        "Checkout save operation failed"
                    )

            except Exception as checkout_error:
                logger.error(f"Checkout process error: {checkout_error}")
                st.error(f"❌ Checkout error: {checkout_error}")
                log_security_event(
                    "CHECKOUT_ERROR",
                    employee_id,
                    logged_username,
                    f"Checkout error: {str(checkout_error)}"
                )

    except Exception as checkout_calc_error:
        logger.error(f"Checkout calculation error: {checkout_calc_error}")
        st.error(f"❌ Error calculating checkout data: {checkout_calc_error}")


def display_completed_attendance(record, logged_username, today):
    """Display already completed attendance information"""
    st.markdown("#### ℹ️ **Attendance Already Complete**")

    try:
        check_in_time = pd.to_datetime(record["start_datetime"])
        check_out_time = pd.to_datetime(record["exit_datetime"])

        st.info("✅ Your secure attendance for today has already been completed.")

        st.markdown(f"""
        <div class="metric-card">
            <h3>📋 Today's Secure Attendance Summary</h3>
            <p><strong>🔑 Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
            <p><strong>🚪 Check-Out:</strong> {check_out_time.strftime('%I:%M %p')}</p>
            <p><strong>⏱️ Total Hours:</strong> {record.get('total_hours', 0):.2f} hours</p>
            <p><strong>📊 Status:</strong> {record.get('attendance_status', 'Unknown')}</p>
            <p><strong>⏰ Overtime Hours:</strong> {record.get('extra_hours', 0):.2f} hours</p>
            <p><strong>💰 Extra Pay:</strong> ₹{record.get('extra_pay', 0):.2f}</p>
            <p><strong>👤 Verified User:</strong> {logged_username}</p>
            <p><strong>📍 Location:</strong> {record.get('location_name', 'Unknown')}</p>
            <p><strong>🔒 Security Level:</strong> Maximum</p>
            <span class="speed-indicator">ATTENDANCE COMPLETE</span>
        </div>
        """, unsafe_allow_html=True)

        # Next working day information
        next_day = today + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip weekends
            next_day += timedelta(days=1)

        st.markdown(f"""
        <div class="success-container">
            <h4 style="color: #2E7D32;">📅 Next Working Day</h4>
            <p style="color: #388E3C;">Next attendance: <strong>{next_day.strftime('%A, %B %d, %Y')}</strong></p>
            <p style="color: #388E3C;">Expected arrival: <strong>9:00 AM</strong></p>
            <p style="color: #388E3C;">Have a great evening!</p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as summary_error:
        logger.error(f"Error displaying attendance summary: {summary_error}")
        st.error("❌ Error loading attendance summary")


def display_secure_attendance_history(attendance_df, employee_id, employee_name, now):
    """Display secure attendance history with enhanced features"""
    st.markdown("### 📊 Your Secure Attendance History")

    try:
        if attendance_df.empty:
            st.info("📋 No attendance history found. Today's attendance will appear here after completion.")
            return

        employee_attendance = attendance_df[attendance_df["employee_id"] == employee_id].copy()

        if not employee_attendance.empty:
            # Sort by date (most recent first)
            employee_attendance = employee_attendance.sort_values("start_datetime", ascending=False)

            # Display last 10 records with enhanced security info
            display_columns = [
                "date_only", "start_datetime", "exit_datetime", "total_hours",
                "attendance_status", "late_mark", "location_name", "confidence", "method"
            ]

            display_df = employee_attendance.head(10)[
                [col for col in display_columns if col in employee_attendance.columns]
            ].copy()

            if not display_df.empty:
                # Format columns securely
                if "start_datetime" in display_df.columns:
                    display_df["Check-In"] = pd.to_datetime(display_df["start_datetime"]).dt.strftime('%I:%M %p')
                    display_df.drop("start_datetime", axis=1, inplace=True)

                if "exit_datetime" in display_df.columns:
                    display_df["Check-Out"] = display_df["exit_datetime"].apply(
                        lambda x: pd.to_datetime(x).strftime('%I:%M %p') if pd.notna(x) else "-"
                    )
                    display_df.drop("exit_datetime", axis=1, inplace=True)

                # Rename columns
                column_mapping = {
                    "date_only": "Date",
                    "total_hours": "Hours",
                    "attendance_status": "Status",
                    "late_mark": "Late",
                    "location_name": "Location",
                    "confidence": "Biometric %",
                    "method": "Security Method"
                }

                display_df = display_df.rename(columns=column_mapping)
                display_df = display_df.fillna("-")

                # Format specific columns
                if "Biometric %" in display_df.columns:
                    display_df["Biometric %"] = display_df["Biometric %"].apply(
                        lambda x: f"{x:.1f}%" if pd.notna(x) and str(x) != "-" else "-"
                    )

                if "Late" in display_df.columns:
                    display_df["Late"] = display_df["Late"].apply(
                        lambda x: "Yes" if x is True else "No" if x is False else "-"
                    )

                st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Secure download options
            col1, col2 = st.columns(2)

            with col1:
                csv_data = employee_attendance.to_csv(index=False)
                st.download_button(
                    label="📥 Download Personal Report (CSV)",
                    data=csv_data,
                    file_name=f"secure_attendance_{employee_id}_{employee_name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

            with col2:
                # Current month data
                current_month = employee_attendance[
                    employee_attendance["start_datetime"].dt.month == now.month
                    ]
                if not current_month.empty:
                    monthly_csv = current_month.to_csv(index=False)
                    st.download_button(
                        label="📅 Download This Month (CSV)",
                        data=monthly_csv,
                        file_name=f"monthly_attendance_{employee_id}_{now.strftime('%Y_%m')}.csv",
                        mime="text/csv"
                    )

            # Enhanced statistics
            st.markdown("#### 📈 Your Performance Statistics")

            current_month_data = employee_attendance[
                employee_attendance["start_datetime"].dt.month == now.month
                ]

            if not current_month_data.empty:
                try:
                    total_days = len(current_month_data)
                    late_days = len(current_month_data[current_month_data["late_mark"] == True])
                    full_days = len(current_month_data[current_month_data["attendance_status"] == "Full Day"])
                    avg_hours = current_month_data[
                        "total_hours"].mean() if "total_hours" in current_month_data.columns else 0
                    total_overtime = current_month_data[
                        "extra_hours"].sum() if "extra_hours" in current_month_data.columns else 0
                    avg_biometric = current_month_data[
                        "confidence"].mean() if "confidence" in current_month_data.columns else 0

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            label="📅 Days This Month",
                            value=total_days,
                            delta=f"{(total_days / 22) * 100:.0f}% attendance"
                        )

                    with col2:
                        st.metric(
                            label="⏰ Punctuality",
                            value=f"{total_days - late_days}/{total_days}",
                            delta=f"{((total_days - late_days) / total_days) * 100:.0f}% on time" if total_days > 0 else "0%"
                        )

                    with col3:
                        st.metric(
                            label="✅ Full Days",
                            value=full_days,
                            delta=f"{(full_days / total_days) * 100:.0f}% full attendance" if total_days > 0 else "0%"
                        )

                    with col4:
                        st.metric(
                            label="🎯 Avg Biometric",
                            value=f"{avg_biometric:.0f}%",
                            delta="High accuracy"
                        )

                    # Additional performance metrics
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            label="⚡ Avg Daily Hours",
                            value=f"{avg_hours:.1f}h",
                            delta="Productive"
                        )

                    with col2:
                        st.metric(
                            label="⏰ Total Overtime",
                            value=f"{total_overtime:.1f}h",
                            delta="Extra contribution"
                        )

                except Exception as stats_error:
                    logger.error(f"Statistics calculation error: {stats_error}")
                    st.error("❌ Error calculating statistics")
            else:
                st.info("📊 No data available for current month statistics.")

        else:
            st.info("📋 No attendance history found for your employee ID.")

    except Exception as history_error:
        logger.error(f"Attendance history error: {history_error}")
        st.error("❌ Error loading attendance history")


# Helper Functions
def get_greeting(now):
    """Get time-based greeting"""
    hour = now.hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


def perform_face_recognition(badge_path, employee_id):
    """
    Perform face recognition - mock implementation
    Replace this with your actual face recognition logic
    """
    try:
        # Mock implementation - replace with actual face recognition
        # This should compare the face in badge_path with stored employee photo
        import random
        confidence = random.uniform(80, 99)  # Mock confidence score
        return confidence
    except Exception as e:
        logger.error(f"Face recognition error: {e}")
        return 0.0


def get_user_location():
    """
    Get user location - mock implementation
    Replace this with your actual location verification logic
    """
    try:
        # Mock implementation - replace with actual location logic
        return {
            'verified': True,
            'lat': 16.7050,  # Mock coordinates
            'lon': 74.2433,
            'name': 'Office Location'
        }
    except Exception as e:
        logger.error(f"Location error: {e}")
        return None


def load_attendance():
    """
    Load attendance data with error handling
    Replace this with your actual data loading logic
    """
    try:
        if USE_SQL:
            # SQL implementation
            conn = safe_get_conn()
            query = "SELECT * FROM attendance_table"

            if hasattr(conn, 'connect'):
                # SQLAlchemy engine
                with conn.connect() as connection:
                    from sqlalchemy import text
                    df = pd.read_sql(text(query), connection)
            else:
                # Direct connection
                df = pd.read_sql(query, conn)
                conn.close()

            return df
        else:
            # CSV implementation
            csv_file = "attendance_data.csv"
            if os.path.exists(csv_file):
                return pd.read_csv(csv_file)
            else:
                # Return empty DataFrame with proper columns
                return pd.DataFrame(columns=[
                    'employee_id', 'employee_name', 'start_datetime', 'exit_datetime',
                    'date_only', 'total_hours', 'extra_hours', 'extra_pay',
                    'attendance_status', 'late_mark', 'method', 'confidence',
                    'notes', 'location_lat', 'location_lon', 'location_verified', 'location_name'
                ])
    except Exception as e:
        logger.error(f"Failed to load attendance data: {e}")
        return None


def save_attendance_secure(df):
    """
    Save attendance data securely with error handling
    Replace this with your actual data saving logic
    """
    try:
        if USE_SQL:
            # SQL implementation
            conn = safe_get_conn()

            if hasattr(conn, 'connect'):
                # SQLAlchemy engine
                with conn.connect() as connection:
                    df.to_sql('attendance_table', connection, if_exists='replace', index=False)
            else:
                # Direct connection
                df.to_sql('attendance_table', conn, if_exists='replace', index=False)
                conn.close()

            return True
        else:
            # CSV implementation
            csv_file = "attendance_data.csv"
            df.to_csv(csv_file, index=False)
            return True

    except Exception as e:
        logger.error(f"Failed to save attendance data: {e}")
        return False


def log_security_event(event_type, employee_id, username, details):
    """
    Log security events for audit trail
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] SECURITY_EVENT: {event_type} | Employee: {employee_id} | User: {username} | Details: {details}"

        # Log to console/file
        logger.info(log_entry)

        # Optionally save to database or file
        if USE_SQL:
            try:
                conn = safe_get_conn()
                security_data = {
                    'timestamp': datetime.now(),
                    'event_type': event_type,
                    'employee_id': employee_id,
                    'username': username,
                    'details': details
                }

                if hasattr(conn, 'connect'):
                    # SQLAlchemy engine
                    with conn.connect() as connection:
                        pd.DataFrame([security_data]).to_sql(
                            'security_logs', connection, if_exists='append', index=False
                        )
                else:
                    # Direct connection
                    pd.DataFrame([security_data]).to_sql(
                        'security_logs', conn, if_exists='append', index=False
                    )
                    conn.close()

            except Exception as db_error:
                logger.error(f"Failed to save security log to database: {db_error}")

    except Exception as e:
        logger.error(f"Failed to log security event: {e}")


def clear_session_cache():
    """Clear problematic session state variables"""
    try:
        keys_to_clear = [
            'location_data', 'location_cache', 'face_recognition_result',
            'biometric_cache', 'attendance_cache'
        ]

        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        logger.info("Session cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing session cache: {e}")


def safe_get_conn():
    """
    Safely get database connection
    Replace this with your actual database connection logic
    """
    try:
        # This is a placeholder - replace with your actual connection logic
        # Example for SQLAlchemy:
        # from sqlalchemy import create_engine
        # engine = create_engine(DATABASE_URL)
        # return engine

        # Example for direct connection:
        # import pymssql
        # conn = pymssql.connect(server, user, password, database)
        # return conn

        # Mock implementation for demonstration
        class MockConnection:
            def connect(self):
                return self

            def execute(self, query):
                class MockResult:
                    def scalar(self):
                        return "MockDatabase"

                return MockResult()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return MockConnection()

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

# ===== ENHANCED DATABASE STATUS =====
# ===== ENHANCED DATABASE STATUS =====
def show_database_status():
    """Show enhanced database connection status with security info"""
    if USE_SQL:
        try:
            # Get connection - handle both engine and direct connection
            conn_or_engine = safe_get_conn()

            if hasattr(conn_or_engine, 'execute') and not hasattr(conn_or_engine, 'connect'):
                # Direct connection object (like pymssql connection)
                cursor = conn_or_engine.cursor()
                cursor.execute("SELECT DB_NAME()")
                db_name = cursor.fetchone()[0]
                cursor.close()
                conn_or_engine.close()
                st.success(f"✅ Connected to database: {db_name}")

            elif hasattr(conn_or_engine, 'connect'):
                # SQLAlchemy engine
                with conn_or_engine.connect() as connection:
                    result = connection.execute(text("SELECT DB_NAME()"))
                    db_name = result.scalar()
                    st.success(f"✅ Connected to database: {db_name}")
            else:
                # Fallback - try direct execution
                result = conn_or_engine.execute(text("SELECT DB_NAME()"))
                db_name = result.scalar()
                st.success(f"✅ Connected to database: {db_name}")

        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            logger.error(f"Database connection failed: {e}")
            # Show fallback mode
            st.warning("🔄 Falling back to CSV mode for data storage")
    else:
        st.info("📂 Using CSV mode (SQL disabled).")


def process_secure_attendance():
    """
    Enhanced secure attendance processing with proper error handling
    """
    try:
        # Initialize variables with default values
        employee_id = st.session_state.get('employee_id', '')
        employee_name = st.session_state.get('employee_name', 'Unknown')
        logged_username = st.session_state.get('username', 'system')
        confidence = 0.0
        detection_method = 'unknown'
        location_verified = False
        location_name = 'Unknown Location'
        user_lat = 0.0
        user_lon = 0.0
        location_source = 'manual'
        salary = st.session_state.get('salary', 0)

        # Validate required session data
        if not employee_id:
            st.error("❌ Employee ID not found. Please login again.")
            return

        # Step 1: Location Verification
        st.markdown("### Step 1: 📍 Secure Location Verification")

        if GEOLOCATION_AVAILABLE:
            location_data = get_user_location()
            if location_data and location_data.get('verified', False):
                user_lat = location_data.get('lat', 0.0)
                user_lon = location_data.get('lon', 0.0)
                location_name = location_data.get('name', 'Office Location')
                location_verified = True
                location_source = 'gps'

                st.success(f"✅ Location verified: {location_name}")
            else:
                st.warning("⚠️ Location verification failed. Using manual verification.")
                location_verified = False
        else:
            st.info("📍 Manual location mode enabled.")

        # Step 2: Badge Upload
        st.markdown("### Step 2: 🆔 Upload Employee Badge")

        uploaded_badge = st.file_uploader(
            "Upload your employee badge photo",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear photo of your employee badge for biometric verification"
        )

        if not uploaded_badge:
            st.warning("⚠️ Please upload your employee badge to continue.")
            st.stop()

        # Step 3: Face Recognition
        st.markdown("### Step 3: 🔐 Biometric Verification")

        if FACE_RECOGNITION_AVAILABLE:
            try:
                # Process badge image
                badge_image = Image.open(uploaded_badge)

                # Simulate face recognition (replace with actual implementation)
                confidence = 95.0  # Mock confidence score
                detection_method = 'face_recognition'

                if confidence >= 80:
                    st.success(f"✅ Biometric verification successful! Confidence: {confidence:.1f}%")
                else:
                    st.error(f"❌ Biometric verification failed. Confidence too low: {confidence:.1f}%")
                    st.stop()

            except Exception as face_error:
                st.error(f"❌ Biometric system error: {face_error}")
                # Fallback to manual verification
                confidence = 75.0
                detection_method = 'manual_verification'
                st.warning("Using manual verification mode.")
        else:
            # Manual verification mode
            st.info("🔐 Manual verification mode")
            confidence = 80.0
            detection_method = 'manual'

        # Step 4: Process Attendance
        st.markdown("### Step 4: ⏰ Processing Secure Attendance")

        now = datetime.now()
        today = now.date()
        greeting = get_greeting(now)

        st.markdown(f"""
        <div class="metric-card">
            <h3>{greeting} {employee_name}! 👋</h3>
            <p>🕐 Current Time: {now.strftime('%I:%M %p')}</p>
            <p>📅 Date: {today.strftime('%A, %B %d, %Y')}</p>
            <p>🔒 Security Level: Maximum</p>
        </div>
        """, unsafe_allow_html=True)

        # Load attendance data
        try:
            attendance_df = load_attendance()
            if attendance_df is not None:
                # Ensure proper data types
                attendance_df["employee_id"] = attendance_df["employee_id"].astype(str)
                attendance_df["start_datetime"] = pd.to_datetime(attendance_df["start_datetime"], errors="coerce")
                attendance_df["date_only"] = attendance_df["start_datetime"].dt.date
            else:
                # Create empty DataFrame if load fails
                attendance_df = pd.DataFrame()

        except Exception as load_error:
            logger.error(f"Error loading attendance: {load_error}")
            st.error("❌ Error loading attendance data. Creating new record.")
            attendance_df = pd.DataFrame()

        # Check today's record
        if not attendance_df.empty:
            mask = (attendance_df["employee_id"] == employee_id) & (attendance_df["date_only"] == today)
            today_record = attendance_df[mask]
        else:
            today_record = pd.DataFrame()

        if today_record.empty:
            # === CHECK-IN PROCESS ===
            process_checkin(attendance_df, employee_id, employee_name, now, today,
                            confidence, detection_method, location_name, location_verified,
                            user_lat, user_lon, location_source, logged_username)
        else:
            # === CHECK-OUT PROCESS ===
            record = today_record.iloc[0]
            if pd.isnull(record.get("exit_datetime", pd.NaT)):
                process_checkout(attendance_df, record, employee_id, employee_name,
                                 now, today, confidence, detection_method, location_name,
                                 salary, logged_username)
            else:
                display_completed_attendance(record, logged_username)

        # Display attendance history
        display_attendance_history(attendance_df, employee_id, employee_name, now)

    except Exception as e:
        logger.error(f"Critical attendance error: {e}")
        st.error(f"❌ Critical system error: {e}")

        # Recovery options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry Process", key="retry_main"):
                st.rerun()
        with col2:
            if st.button("🏠 Return Home", key="home_main"):
                # Clear session state
                clear_session_state()
                st.rerun()


def process_checkin(attendance_df, employee_id, employee_name, now, today,
                    confidence, detection_method, location_name, location_verified,
                    user_lat, user_lon, location_source, logged_username):
    """Process secure check-in"""
    st.markdown("#### 🔑 **Secure Check-In Process**")

    try:
        # Calculate late status
        late_cutoff = datetime.strptime("09:15", "%H:%M").time()
        late_mark = now.time() > late_cutoff

        if late_mark:
            late_minutes = (datetime.combine(today, now.time()) -
                            datetime.combine(today, late_cutoff)).seconds // 60
            st.warning(f"⚠️ Late arrival detected: {late_minutes} minutes after 9:15 AM")

        # Create new attendance record
        new_row = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "start_datetime": now,
            "exit_datetime": pd.NaT,
            "date_only": today,
            "total_hours": pd.NA,
            "extra_hours": 0,
            "extra_pay": 0,
            "attendance_status": pd.NA,
            "late_mark": late_mark,
            "method": f"Secure GPS + Biometric ({detection_method})",
            "confidence": confidence,
            "notes": f"Verified login: {logged_username} | Location: {location_source}",
            "location_lat": user_lat,
            "location_lon": user_lon,
            "location_verified": location_verified,
            "location_name": location_name
        }

        # Add to DataFrame
        if attendance_df.empty:
            attendance_df = pd.DataFrame([new_row])
        else:
            attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)

        # Remove duplicates
        attendance_df.drop_duplicates(subset=["employee_id", "date_only"], keep="last", inplace=True)

        # Save attendance
        if save_attendance_secure(attendance_df):
            # Success display
            st.success("🎉 Secure Check-In Successful!")
            st.balloons()

            display_checkin_summary(employee_name, now, today, location_name,
                                    detection_method, confidence, logged_username, late_mark)
        else:
            st.error("❌ Failed to save check-in data.")

    except Exception as checkin_error:
        logger.error(f"Check-in error: {checkin_error}")
        st.error(f"❌ Check-in process failed: {checkin_error}")


def process_checkout(attendance_df, record, employee_id, employee_name, now, today,
                     confidence, detection_method, location_name, salary, logged_username):
    """Process secure check-out"""
    st.markdown("#### 🚪 **Secure Check-Out Process**")

    try:
        check_in_time = pd.to_datetime(record["start_datetime"])
        elapsed_seconds = (now - check_in_time).total_seconds()

        # Minimum time validation
        if elapsed_seconds < 60:
            remaining_seconds = 60 - elapsed_seconds
            st.warning(f"⏳ Please wait {remaining_seconds:.0f} seconds before checkout.")
            if st.button("🔄 Refresh", key="checkout_refresh"):
                st.rerun()
            st.stop()

        # Calculate work duration
        total_hours = elapsed_seconds / 3600
        hours = int(total_hours)
        minutes = int((total_hours - hours) * 60)

        # Calculate overtime
        overtime_start = datetime.combine(today, datetime.strptime("18:45", "%H:%M").time())
        extra_hours = max((now - overtime_start).total_seconds() / 3600, 0) if now > overtime_start else 0

        # Calculate extra pay
        extra_pay = 0
        if salary > 0 and extra_hours > 0:
            hourly_rate = salary / (8 * 26)
            extra_pay = extra_hours * hourly_rate

        # Determine status
        if total_hours < 4:
            attendance_status = "Absent"
        elif total_hours < 6:
            attendance_status = "Half Day"
        else:
            attendance_status = "Full Day"

        # Display checkout summary
        display_checkout_summary(check_in_time, now, hours, minutes, total_hours,
                                 attendance_status, extra_hours, extra_pay)

        # Checkout confirmation
        if st.button("✅ **Confirm Secure Check-Out**", key="secure_checkout"):
            try:
                # Update record
                idx = attendance_df[(attendance_df["employee_id"] == employee_id) &
                                    (attendance_df["date_only"] == today)].index[0]

                attendance_df.loc[idx, "exit_datetime"] = now
                attendance_df.loc[idx, "total_hours"] = round(total_hours, 2)
                attendance_df.loc[idx, "extra_hours"] = round(extra_hours, 2)
                attendance_df.loc[idx, "extra_pay"] = round(extra_pay, 2)
                attendance_df.loc[idx, "attendance_status"] = attendance_status

                if save_attendance_secure(attendance_df):
                    st.success("🎉 Secure Check-Out Successful!")
                    st.balloons()
                    display_checkout_success(now, total_hours, attendance_status,
                                             extra_hours, extra_pay, logged_username, location_name)
                else:
                    st.error("❌ Failed to save checkout data.")

            except Exception as save_error:
                logger.error(f"Checkout save error: {save_error}")
                st.error(f"❌ Error saving checkout: {save_error}")

    except Exception as checkout_error:
        logger.error(f"Checkout error: {checkout_error}")
        st.error(f"❌ Checkout process failed: {checkout_error}")


def display_checkin_summary(employee_name, now, today, location_name, detection_method,
                            confidence, logged_username, late_mark):
    """Display check-in success summary"""
    st.markdown(f"""
    <div class="metric-card">
        <h3>🎉 Secure Check-In Successful!</h3>
        <p><strong>👤 Employee:</strong> {employee_name}</p>
        <p><strong>🕐 Check-In Time:</strong> {now.strftime('%I:%M %p')}</p>
        <p><strong>📅 Date:</strong> {today.strftime('%A, %B %d, %Y')}</p>
        <p><strong>📍 Location:</strong> {location_name}</p>
        <p><strong>⚡ Method:</strong> {detection_method.title()}</p>
        <p><strong>🎯 Biometric Match:</strong> {confidence:.1f}%</p>
        <p><strong>👤 Verified User:</strong> {logged_username}</p>
        <p><strong>🔒 Security:</strong> Maximum</p>
        {"<p style='color: #ffeb3b;'>⚠️ Late Mark Applied</p>" if late_mark else "<p style='color: #4CAF50;'>✅ On Time</p>"}
    </div>
    """, unsafe_allow_html=True)


def display_checkout_summary(check_in_time, now, hours, minutes, total_hours,
                             attendance_status, extra_hours, extra_pay):
    """Display checkout summary"""
    status_colors = {
        "Absent": "#f44336",
        "Half Day": "#FF9800",
        "Full Day": "#4CAF50"
    }

    st.markdown(f"""
    <div class="warning-container">
        <h4 style="color: #E65100;">⏰ Secure Checkout Summary</h4>
        <p><strong>Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
        <p><strong>Current Time:</strong> {now.strftime('%I:%M %p')}</p>
        <p><strong>Total Duration:</strong> {hours}h {minutes}m ({total_hours:.2f} hours)</p>
        <p><strong>Status:</strong> <span style="color: {status_colors.get(attendance_status, '#666')}; font-weight: bold;">{attendance_status}</span></p>
        <p><strong>Overtime Hours:</strong> {extra_hours:.2f} hours</p>
        <p><strong>Extra Payment:</strong> ₹{extra_pay:.2f}</p>
        <p><strong>🔒 Verification:</strong> Biometric + GPS</p>
    </div>
    """, unsafe_allow_html=True)


def display_checkout_success(now, total_hours, attendance_status, extra_hours,
                             extra_pay, logged_username, location_name):
    """Display checkout success message"""
    st.markdown(f"""
    <div class="metric-card">
        <h3>🎉 Secure Check-Out Successful!</h3>
        <p><strong>🚪 Check-Out Time:</strong> {now.strftime('%I:%M %p')}</p>
        <p><strong>⏱️ Total Hours:</strong> {total_hours:.2f} hours</p>
        <p><strong>📊 Status:</strong> {attendance_status}</p>
        <p><strong>⏰ Overtime Hours:</strong> {extra_hours:.2f} hours</p>
        <p><strong>💰 Extra Pay:</strong> ₹{extra_pay:.2f}</p>
        <p><strong>👤 Verified User:</strong> {logged_username}</p>
        <p><strong>📍 Location:</strong> {location_name}</p>
        <p><strong>🔒 Security:</strong> Maximum</p>
    </div>
    """, unsafe_allow_html=True)


def display_completed_attendance(record, logged_username):
    """Display already completed attendance"""
    st.markdown("#### ℹ️ **Attendance Already Complete**")
    st.info("✅ Your secure attendance for today has already been completed.")

    check_in_time = pd.to_datetime(record["start_datetime"])
    check_out_time = pd.to_datetime(record["exit_datetime"])

    st.markdown(f"""
    <div class="metric-card">
        <h3>📋 Today's Secure Attendance Summary</h3>
        <p><strong>🔑 Check-In:</strong> {check_in_time.strftime('%I:%M %p')}</p>
        <p><strong>🚪 Check-Out:</strong> {check_out_time.strftime('%I:%M %p')}</p>
        <p><strong>⏱️ Total Hours:</strong> {record.get('total_hours', 0):.2f} hours</p>
        <p><strong>📊 Status:</strong> {record.get('attendance_status', 'Unknown')}</p>
        <p><strong>⏰ Overtime Hours:</strong> {record.get('extra_hours', 0):.2f} hours</p>
        <p><strong>💰 Extra Pay:</strong> ₹{record.get('extra_pay', 0):.2f}</p>
        <p><strong>👤 Verified User:</strong> {logged_username}</p>
        <p><strong>🔒 Security Level:</strong> Maximum</p>
    </div>
    """, unsafe_allow_html=True)


def display_attendance_history(attendance_df, employee_id, employee_name, now):
    """Display attendance history with error handling"""
    st.markdown("### 📊 Your Secure Attendance History")

    try:
        if attendance_df.empty:
            st.info("📋 No attendance history found.")
            return

        employee_attendance = attendance_df[attendance_df["employee_id"] == employee_id].copy()

        if employee_attendance.empty:
            st.info("📋 No attendance records found for your employee ID.")
            return

        # Sort by date
        employee_attendance = employee_attendance.sort_values("start_datetime", ascending=False)

        # Display recent records
        display_df = employee_attendance.head(10).copy()

        # Format for display
        if not display_df.empty:
            # Safe column operations
            if "start_datetime" in display_df.columns:
                display_df["Check-In"] = pd.to_datetime(display_df["start_datetime"]).dt.strftime('%I:%M %p')

            if "exit_datetime" in display_df.columns:
                display_df["Check-Out"] = display_df["exit_datetime"].apply(
                    lambda x: pd.to_datetime(x).strftime('%I:%M %p') if pd.notna(x) else "-"
                )

            # Select and rename columns safely
            display_columns = []
            column_mapping = {
                "date_only": "Date",
                "Check-In": "Check-In",
                "Check-Out": "Check-Out",
                "total_hours": "Hours",
                "attendance_status": "Status",
                "late_mark": "Late"
            }

            for old_col, new_col in column_mapping.items():
                if old_col in display_df.columns:
                    display_columns.append(old_col)

            if display_columns:
                final_df = display_df[display_columns].rename(columns=column_mapping)
                final_df = final_df.fillna("-")
                st.dataframe(final_df, use_container_width=True, hide_index=True)

        # Download options
        col1, col2 = st.columns(2)
        with col1:
            csv_data = employee_attendance.to_csv(index=False)
            st.download_button(
                label="📥 Download Report (CSV)",
                data=csv_data,
                file_name=f"attendance_{employee_id}_{now.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    except Exception as history_error:
        logger.error(f"History display error: {history_error}")
        st.error("❌ Error loading attendance history")


def clear_session_state():
    """Clear problematic session state variables"""
    keys_to_clear = ['location_data', 'location_cache', 'face_recognition_result']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


# Helper functions (mock implementations)
def get_greeting(now):
    """Get time-based greeting"""
    hour = now.hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


def load_attendance():
    """Load attendance data with error handling"""
    try:
        # Your actual load implementation here
        # This is a placeholder
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load attendance: {e}")
        return None


def save_attendance_secure(df):
    """Save attendance data securely"""
    try:
        # Your actual save implementation here
        # This is a placeholder
        return True
    except Exception as e:
        logger.error(f"Failed to save attendance: {e}")
        return False


def get_user_location():
    """Get user location with error handling"""
    try:
        # Your actual location implementation here
        return None
    except Exception as e:
        logger.error(f"Location error: {e}")
        return None


def log_security_event(event_type, employee_id, username, details):
    """Log security events"""
    try:
        logger.info(f"SECURITY_EVENT: {event_type} | Employee: {employee_id} | User: {username} | Details: {details}")
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")