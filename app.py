import concurrent.futures
import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
from ai_handler import analyze_size_chart, parse_ai_response, analyze_clothing_reviews
from logic import DatabaseManager, SizeEngine, is_valid_email

def show_measurement_guide():
    with st.expander("Measurement Guide"):
        st.markdown("""
        ### How to measure correctly:
        - **Chest (cm):** Measure around the **fullest part** of your bust. *Don't hold your breath!*
        - **Waist (cm):** Measure around your **natural waistline** (the narrowest part, just above the belly button).
        - **Hips (cm):** Stand with feet together, measure around the **fullest part** of your hips and buttocks.
        
        **Optional Measurements:**
        - *Inseam:* Inner thigh down to your ankle. 
        - *Shoulder:* Across your back from shoulder bone to shoulder bone.
        - *Thigh:* Around the fullest part of your upper leg.
        
        <p style='color: gray; font-size: 0.9rem;'>* Tip: Use a flexible measuring tape and keep it snug but not tight. Keep the tape parallel to the floor.</p>
        """, unsafe_allow_html=True)

# --- Singleton Initialization ---
if 'db' not in st.session_state:
    st.session_state['db'] = DatabaseManager()

if 'engine' not in st.session_state:
    st.session_state['engine'] = SizeEngine(st.session_state['db'])

db = st.session_state['db']
engine = st.session_state['engine']

# --- Page Configuration ---
# בקובץ app.py - השורה הראשונה אחרי ה-Imports
st.set_page_config(
    page_title="MatchMyFit AI",
    page_icon="👕",  
    layout="wide"
)

# --- Modern SaaS UI Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Heebo', -apple-system, sans-serif !important;
    }  
    .hero-container {
        text-align: center;
        padding: 3rem 1.5rem 3rem 1.5rem;
        background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
        border-radius: 24px;
        margin-bottom: 2.5rem;
        border: 1px solid #F1F5F9;
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -1.5px;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        line-height: 1;
    }    
    .hero-title span { color: #4F46E5; } 
    .hero-subtitle {
        font-size: 1.2rem;
        color: #64748B;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
        font-weight: 400;
    }
    .steps-wrapper {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 3.5rem;
        width: 100%;
        max-width: 1000px;
        margin-left: auto;
        margin-right: auto;
    }
    .step-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: left;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .step-card:hover {
        transform: translateY(-5px);
        border-color: #A5B4FC;
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.08);
    }
    .step-number {
        background: #EEF2FF;
        color: #4F46E5;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    .step-title {
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        letter-spacing: -0.5px;
    }
    .step-text {
        color: #64748B;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .stButton>button[kind="primary"] {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 0.6rem 2.5rem !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.25) !important;
    }
    hr { border-color: #F1F5F9 !important; }
    .streamlit-expanderHeader {
        border-radius: 12px !important;
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        color: #334155 !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- HTML Templates ---
hero_html_logged_out = """
<div class="hero-container">
    <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z"></path>
    </svg>
    <div class="hero-title">Match<span>MyFit</span></div>
    <div class="hero-subtitle">Precision sizing using computer vision and your personal measurements.</div>
    <div class="steps-wrapper">
        <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-title">Setup Profile</div>
            <div class="step-text">Register and save your exact body measurements just once.</div>
        </div>
        <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-title">Upload Chart</div>
            <div class="step-text">Found a garment you love? Upload its size guide image.</div>
        </div>
        <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-title">Add Insights</div>
            <div class="step-text">Paste customer reviews to let our AI analyze fit trends (Optional).</div>
        </div>
        <div class="step-card">
            <div class="step-number">4</div>
            <div class="step-title">Get Recommendation</div>
            <div class="step-text">Instantly get your highly accurate size recommendation.</div>
        </div>
    </div>
</div>
"""

hero_html_logged_in = """
<div style="text-align: center; margin-bottom: 2rem; margin-top: 1rem;">
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z"></path>
    </svg>
    <div style="font-size: 2.5rem; font-weight: 800; color: #0F172A; letter-spacing: -1px; line-height: 1; margin-top: 0.5rem;">
        Match<span style="color: #4F46E5;">MyFit</span>
    </div>
</div>
"""

# --- Session State ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# ==========================================
# FLOW 1: USER IS NOT LOGGED IN
# ==========================================
if not st.session_state['user']:
    
    st.markdown(hero_html_logged_out, unsafe_allow_html=True)
    st.info("**Ready to get started?** Click the small arrow ( >> ) in the top left corner to open the menu and Sign In or Create an Account.")
    
    with st.sidebar:
        st.header("Account Management")
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            email_input = st.text_input("Email Address", key="login_email")
            if st.button("Sign In", width="stretch"):
                user_data = db.login_user(email_input)
                if user_data:
                    st.session_state['user'] = user_data
                    st.success(f"Welcome back, {user_data['full_name']}")
                    st.rerun()
                else:
                    st.error("User not found. Please register.")
                    
        with tab_register:
            new_email = st.text_input("New Email")
            new_name = st.text_input("Full Name")
            st.markdown("---")
            show_measurement_guide()
            st.markdown("**Required Measurements (cm)**")
            c1, c2 = st.columns(2)
            waist = c1.number_input("Waist", min_value=0.0, value=72.0)
            chest = c2.number_input("Chest", min_value=0.0, value=90.0)
            hip = c1.number_input("Hip", min_value=0.0, value=98.0)
            height = c2.number_input("Height", min_value=0.0, value=158.0)
            
            st.markdown("**Optional Measurements (cm)**")
            c3, c4 = st.columns(2)
            inseam = c3.number_input("Inseam", min_value=0.0, value=0.0)
            shoulder = c4.number_input("Shoulder", min_value=0.0, value=0.0)
            arm = c3.number_input("Arm Length", min_value=0.0, value=0.0)
            thigh = c4.number_input("Thigh", min_value=0.0, value=0.0)
            
            if st.button("Create Account", width="stretch"):
                if not is_valid_email(new_email):
                    st.error("Please enter a valid email address (e.g., name@example.com).")
                else:
                    user_dict = {
                        'email': new_email, 'full_name': new_name,
                        'waist': waist, 'chest': chest, 'hip': hip,
                        'height': height, 
                        'inseam': inseam if inseam > 0 else None,
                        'shoulder': shoulder if shoulder > 0 else None,
                        'arm': arm if arm > 0 else None,
                        'thigh': thigh if thigh > 0 else None
                    }
                    if db.register_user(user_dict):
                        st.success("Account created successfully. You can now log in.")
                    else:
                        st.error("Email already exists in the system.")

# ==========================================
# FLOW 2: USER IS LOGGED IN
# ==========================================
else:
    u = st.session_state['user']
    
    st.markdown(hero_html_logged_in, unsafe_allow_html=True)
    
    # --- Sidebar Profile Management ---
    with st.sidebar:
        st.header("My Profile")
        st.success("Active Session")
        st.write(f"**Name:** {u['full_name']}")
        st.write(f"**Waist:** {u['waist_circumference']} cm | **Chest:** {u['chest_circumference']} cm")
        
        st.divider()
        with st.expander("Update Measurements"):
            with st.form("update_form"):
                upd_name = st.text_input("Full Name", value=u['full_name'])
                show_measurement_guide()
                st.markdown("**Required (cm)**")
                c5, c6 = st.columns(2)
                upd_waist = c5.number_input("Waist", value=float(u['waist_circumference'] or 0.0))
                upd_chest = c6.number_input("Chest", value=float(u['chest_circumference'] or 0.0))
                upd_hip = c5.number_input("Hip", value=float(u['hip_circumference'] or 0.0))
                upd_height = c6.number_input("Height", value=float(u['height_cm'] or 0.0))
                
                st.markdown("**Optional (Set to 0 if unknown)**")
                c7, c8 = st.columns(2)
                upd_inseam = c7.number_input("Inseam", value=float(u.get('inseam_cm') or 0.0))
                upd_shoulder = c8.number_input("Shoulder", value=float(u.get('shoulder_width') or 0.0))
                upd_arm = c7.number_input("Arm", value=float(u.get('arm_length') or 0.0))
                upd_thigh = c8.number_input("Thigh", value=float(u.get('thigh_circumference') or 0.0))
                
                if st.form_submit_button("Save Changes"):
                    new_measurements = {
                        'full_name': upd_name, 'waist': upd_waist, 'chest': upd_chest,
                        'hip': upd_hip, 'height': upd_height, 
                        'inseam': upd_inseam if upd_inseam > 0 else None,
                        'shoulder': upd_shoulder if upd_shoulder > 0 else None,
                        'arm': upd_arm if upd_arm > 0 else None,
                        'thigh': upd_thigh if upd_thigh > 0 else None
                    }
                    if db.update_user_measurements(u['email'], new_measurements):
                        st.session_state['user'] = db.login_user(u['email'])
                        st.success("Profile updated.")
                        st.rerun()
                    else:
                        st.error("Failed to update.")

        if st.button("Sign Out", type="secondary", width="stretch"):
            st.session_state['user'] = None
            st.rerun()
            
        st.divider()
        if st.button("Delete Account", type="primary", width="stretch"):
            if db.delete_user(u['email']):
                st.session_state['user'] = None
                st.rerun()

    # --- Main Application Tabs ---
    tab_scan, tab_closet = st.tabs(["Scan Garment", "My Closet"])

    # ------------------------------------------
    # TAB 1: Scan Garment
    # ------------------------------------------
    with tab_scan:
        st.markdown("<h3 class='section-header'>1. Garment Details</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", engine.get_garment_categories())
        with col2:
            fit = st.selectbox("Fit Preference", ["slim", "regular", "relaxed"], index=1)
            
        st.markdown("#### Fabric Composition")
        fc1, fc2, fc3, fc4 = st.columns([3, 1, 3, 1])
        
        with fc1:
            main_fabric = st.selectbox("Main Fabric", db.get_all_fabric_names())
        with fc2:
            main_pct = st.number_input("Main %", min_value=0, max_value=100, value=100)
        with fc3:
            stretchy_options = ["None (0%)", "Spandex / Elastane / Lycra", "Polyamide / Nylon"]
            stretch_type = st.selectbox("Stretch Component", stretchy_options, help="Look at the label.")
        with fc4:
            elastane_pct = st.number_input("Stretch %", min_value=0, max_value=100, value=0)

        st.markdown("<h3 class='section-header'>2. Size Chart Analysis</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload product size chart", type=['png', 'jpg', 'jpeg'])

        if uploaded_file:
            col_img, col_res = st.columns([1, 1])
            with col_img:
                img = Image.open(uploaded_file)
                st.image(img, use_container_width=True)
            
            with col_res:
                st.write("Ready to analyze your perfect fit.")
                with st.expander("Have customer reviews? Paste them here for AI analysis (Optional)"):
                    reviews_input = st.text_area(
                        "Paste reviews here:", 
                        placeholder="e.g. 'Loved the pants but they run a bit small in the waist...'",
                        height=130
                    )
                
                if st.button("Calculate Optimal Size", type="primary", width="stretch"):
                    # --- Validation Block Restored Here ---
                    total_pct = main_pct + elastane_pct
                    if total_pct > 100:
                        st.error("Validation Error: The total fabric percentage cannot exceed 100%.")
                        st.stop()
                    elif stretch_type == "None (0%)" and elastane_pct > 0:
                        st.error("Logical Error: If 'None' is selected, the stretch percentage must be 0.")
                        st.stop()
                    elif total_pct == 0:
                        st.error("Validation Error: A garment cannot be made of 0% fabric.")
                        st.stop()
                        
                    with st.spinner("Analyzing size chart & measurements in parallel..."):
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future_chart = executor.submit(analyze_size_chart, img)
                            future_reviews = None
                            
                            if reviews_input.strip():
                                future_reviews = executor.submit(analyze_clothing_reviews, reviews_input)
                                
                            raw_res = future_chart.result()
                            size_chart_dict = parse_ai_response(raw_res)
                        
                        if size_chart_dict and "error" in size_chart_dict:
                            st.error("Invalid Image: This does not look like a valid size chart. Please upload a clear picture.")
                        elif size_chart_dict:
                            result = engine.find_best_size(
                                user_profile=st.session_state['user'],
                                garment_category=category,
                                main_fabric=main_fabric,
                                main_pct=main_pct,
                                stretch_type=stretch_type,
                                stretch_pct=elastane_pct,
                                size_chart=size_chart_dict,
                                fit_pref=fit
                            )
                            st.divider()
                            final_rec = result["recommendation"]
                            
                            if final_rec == "Consult Size Chart":
                                st.warning("Measurement Out of Bounds: Your measurements do not fit this garment's standard size range.")
                            else:
                                st.success(f"### Recommended Size: **{final_rec}**")
                                
                                # --- Save successful scan to database ---
                                db.save_scan(u['email'], category, final_rec, main_fabric, size_chart_data=size_chart_dict)
                                
                                if future_reviews:
                                    with st.spinner("Fetching AI insights..."):
                                        reviews_data = parse_ai_response(future_reviews.result())
                                        if reviews_data and "overall_fit" in reviews_data:
                                            fit_trend = reviews_data["overall_fit"]
                                            problem_area = reviews_data.get("problem_area")
                                            
                                            if fit_trend == "runs_small":
                                                st.warning(f"**AI Insight:** Customers report this item runs small" + 
                                                           (f", especially in the {problem_area}." if problem_area else ".") + 
                                                           " Consider sizing up.")
                                            elif fit_trend == "runs_large":
                                                st.warning(f"**AI Insight:** Customers report this item runs large" + 
                                                           (f", especially in the {problem_area}." if problem_area else ".") + 
                                                           " Consider sizing down.")
                                            elif fit_trend == "true_to_size":
                                                st.info("**AI Insight:** Customers report this item fits exactly true to size.")
                                
                            with st.expander("View Calculation Breakdown"):
                                st.json(result["details"])
                        else:
                            st.error("Processing Error: Failed to extract valid sizing data.")
        # --- Disclaimer ---
        st.markdown("""
            <div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #64748B; font-size: 1rem; border-top: 1px solid #F1F5F9; line-height: 1.5;">
                <b>Disclaimer:</b> MatchMyFit AI provides sizing recommendations based on general pattern-making principles and AI analysis. Variations in brand manufacturing, fabric elasticity, and user measurement accuracy may affect the final fit. This tool is a portfolio project intended for estimation purposes only.
            </div>
        """, unsafe_allow_html=True)

    # ------------------------------------------
    # TAB 2: My Closet (Dashboard)
    # ------------------------------------------
    with tab_closet:
        st.markdown("<h3 class='section-header'>Your Sizing History</h3>", unsafe_allow_html=True)
        
        history_data = db.get_user_history(u['user_id'])
        
        if not history_data:
            st.info("Your closet is empty. Scan your first garment to see your history here!")
        else:
            st.dataframe(history_data, use_container_width=True, hide_index=True)
            
            st.divider()
            
            st.markdown("#### Your Most Common Sizes")
            sizes_only = [item['Size'] for item in history_data]
            size_counts = {size: sizes_only.count(size) for size in set(sizes_only)}
            
            df_sizes = pd.DataFrame(list(size_counts.items()), columns=['Size', 'Scans'])
            
            chart = alt.Chart(df_sizes).mark_bar(
                color='#4F46E5', 
                size=60,
                cornerRadiusTopLeft=6, 
                cornerRadiusTopRight=6
            ).encode(
                x=alt.X('Size', axis=alt.Axis(labelAngle=0, title=''), sort='-y'),
                y=alt.Y('Scans', axis=alt.Axis(tickMinStep=1, title='Items Count')),
                tooltip=['Size', 'Scans']
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)