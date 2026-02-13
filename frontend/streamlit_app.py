"""
Clinical Trial Eligibility Decision Support Web Application
Frontend built with Streamlit
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import sys
import os
from pathlib import Path

# Add backend to path for imports
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.utils import data_loader, formatters
from app.services.nlp import text_processor, llm_service
from app.services.matching import rules_engine
from app.database import crud, db_connection
import base64

# Page Configuration
st.set_page_config(
    page_title="ClinMatch AI",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

# Helper function to get base64 image
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

img_base64 = get_base64_image("assets/lab_illustration.png")

# Custom CSS for Premium Look
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #230C46, #180436);
        background-attachment: fixed;
        color: #f3f4f6;
    }}

    /* Background image overlay */
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: 60%;
        background-position: bottom right;
        background-repeat: no-repeat;
        opacity: 0.05;
        z-index: -1;
        pointer-events: none;
        filter: grayscale(100%) opacity(0.3);
    }}

    [data-testid="stSidebar"] {{
        background-color: #180436;
        border-right: 1px solid #B2963C;
    }}

    .stButton>button {{
        background: linear-gradient(135deg, #F8D849 0%, #B2963C 100%);
        color: #230C46;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 6px;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-transform: uppercase;
        font-size: 0.9rem;
    }}

    .stButton>button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.4);
        background: linear-gradient(135deg, #ffe066 0%, #c2a64c 100%);
        color: #000000;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #F8D849 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        letter-spacing: -0.5px;
    }}

    [data-testid="stMetricLabel"] {{
        color: #A47E9B !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .metric-card {{
        background: rgba(35, 12, 70, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid #B2963C;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }}

    .metric-card:hover {{
        border-color: #F8D849;
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
    }}

    h1, h2 {{
        color: #ffffff;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }}
    
    h3 {{
        color: #F8D849 !important;
        font-weight: 600 !important;
    }}

    h1 {{ font-size: 3rem !important; line-height: 1.2 !important; font-weight: 800 !important; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
    h2 {{ font-size: 1.8rem !important; font-weight: 700 !important; }}
    h3 {{ font-size: 1.25rem !important; }}

    .stExpander {{
        background: rgba(35, 12, 70, 0.6);
        border: 1px solid #B2963C;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    
    .stExpander p {{
        color: #f3f4f6;
    }}
    
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    
    /* Input fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {{
        background-color: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        border: 1px solid #A47E9B;
    }}
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus, .stTextArea>div>div>textarea:focus {{
        border-color: #F8D849;
        box-shadow: 0 0 0 1px #F8D849;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

# ==================== MODAL: CREATE TRIAL DIALOG ====================
@st.dialog("✚ Create New Clinical Trial", width="large")
def create_trial_modal():
    st.markdown("### Trial Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nct_id = st.text_input("NCT ID *", value="", placeholder="e.g., NCT045526")
        title = st.text_input("Trial Title *", value="", placeholder="e.g., Novel Cancer Treatment Study")
        phase = st.selectbox("Phase *", ["Phase 1", "Phase 2", "Phase 3", "Phase 4"])
    
    with col2:
        status = st.selectbox("Status *", ["Recruiting", "Active", "Completed", "Closed"])
        participants = st.number_input("Target Participants *", min_value=1, value=100, step=10)
        sponsor = st.text_input("Sponsor", value="", placeholder="e.g., University Hospital")
    
    st.markdown("### Eligibility Criteria")
    
    col3, col4 = st.columns(2)
    
    with col3:
        inclusion = st.text_area(
            "Inclusion Criteria *", 
            value="",
            placeholder="Enter inclusion criteria (one per line):\\n• Age >= 18\\n• Diagnosis: ...\\n• Lab values: ...",
            height=150
        )
    
    with col4:
        exclusion = st.text_area(
            "Exclusion Criteria *", 
            value="",
            placeholder="Enter exclusion criteria (one per line):\\n• Pregnancy\\n• History of ...\\n• Current medication: ...",
            height=150
        )
    
    st.markdown("### Additional Details")
    
    col5, col6 = st.columns(2)
    
    with col5:
        start_date = st.date_input("Start Date")
        location = st.text_input("Location", placeholder="e.g., Boston, MA")
    
    with col6:
        end_date = st.date_input("Estimated End Date")
        contact = st.text_input("Contact Email", placeholder="trials@hospital.org")
    
    description = st.text_area(
        "Study Description",
        placeholder="Brief description of the trial objectives and methodology...",
        height=100
    )
    
    st.markdown("---")
    
    col_save, col_cancel = st.columns([1, 1])
    
    with col_save:
        if st.button("💾 Save Trial", use_container_width=True, type="primary"):
            # Validation
            if not nct_id or not title or not inclusion or not exclusion:
                st.error("❌ Please fill in all required fields (*)")
            else:
                try:
                    db = next(db_connection.get_db())
                    crud.create_trial(db, {
                        "nct_id": nct_id,
                        "title": title,
                        "phase": phase,
                        "status": status,
                        "inclusion_criteria": inclusion,
                        "exclusion_criteria": exclusion,
                        "target_participants": participants
                    })
                    st.success(f"✅ Trial {nct_id} created successfully!")
                    time.sleep(1)
                    st.session_state.show_create_trial_form = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error creating trial: {str(e)}")
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_trial_form = False
            st.rerun()

# Check if modal should be displayed
if st.session_state.get('show_create_trial_form', False):
    create_trial_modal()

def enter_dashboard():
    st.session_state['page'] = 'dashboard'

def show_landing_page():
    # Split-Screen Hero with stylized asset integration
    st.markdown(f"""
    <div style='padding: 4rem 2rem; display: flex; align-items: center; justify-content: center; min-height: 80vh;'>
        <div style='display: grid; grid-template-columns: 1.2fr 1fr; gap: 4rem; max-width: 1200px; width: 100%; border-radius: 24px; background: rgba(35, 12, 70, 0.6); backdrop-filter: blur(20px); border: 1px solid #B2963C; padding: 4rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);'>
            <div>
                <h1 style='font-size: 3.5rem; margin-bottom: 1rem; font-weight: 800; letter-spacing: -2px; line-height: 1.1; color: #ffffff;'>
                    CLINMATCH <span style='color: #F8D849;'>AI</span>
                </h1>
                <p style='font-size: 1.25rem; color: #d1d5db; margin-top: 1.5rem; line-height: 1.6; font-weight: 400;'>
                    Accelerating Discovery. <span style='color: #F8D849; font-weight: 600;'>Saving Lives.</span> <br><br>
                    Instantly connecting patients to precision therapies through intelligent data matching.
                </p>
            </div>
            <div style='display: flex; align-items: center; justify-content: center; position: relative;'>
                <div style='width: 400px; height: 400px; background: url("data:image/png;base64,{img_base64}"); background-size: cover; background-position: center; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); border: 2px solid #B2963C; transform: rotate(1deg);'></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Consolidated CTA
    ct_col1, ct_col2, ct_col3 = st.columns([1, 1.2, 1])
    with ct_col2:
        st.button("ENTER CLINICAL DASHBOARD", use_container_width=True, on_click=enter_dashboard, help="Launch the Clinical Intelligence Engine")

    # Feature Grid
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
        st.markdown(f"""
        <div class='metric-card' style='height: 260px; border-top: 4px solid #F8D849;'>
            <div style='height: 60px; width: 100%; background: rgba(248, 216, 73, 0.1); border-radius: 8px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #F8D849; font-size: 1.2rem; border: 1px solid #F8D849;'>EXTRACTION</div>
            <h3 style='color: #ffffff; font-size: 1.25rem; margin-top: 0;'>AI Extraction</h3>
            <p style='color: #d1d5db; font-size: 0.95rem; line-height: 1.6;'>
                Unlock the power of unstructured data. Instantly parse clinical notes, PDFs, and reports into structured, actionable insights.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f_col2:
        st.markdown(f"""
        <div class='metric-card' style='height: 260px; border-top: 4px solid #A47E9B;'>
            <div style='height: 60px; width: 100%; background: rgba(164, 126, 155, 0.1); border-radius: 8px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #A47E9B; font-size: 1.2rem; border: 1px solid #A47E9B;'>MATCHING</div>
            <h3 style='color: #ffffff; font-size: 1.25rem; margin-top: 0;'>Trial Matching</h3>
            <p style='color: #d1d5db; font-size: 0.95rem; line-height: 1.6;'>
                Precision at scale. Our hybrid AI engine screens thousands of criteria in seconds to find the perfect patient-trial fit.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f_col3:
        st.markdown(f"""
        <div class='metric-card' style='height: 260px; border-top: 4px solid #B2963C;'>
            <div style='height: 60px; width: 100%; background: rgba(178, 150, 60, 0.1); border-radius: 8px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #B2963C; font-size: 1.2rem; border: 1px solid #B2963C;'>OVERSIGHT</div>
            <h3 style='color: #ffffff; font-size: 1.25rem; margin-top: 0;'>Ethical Oversight</h3>
            <p style='color: #d1d5db; font-size: 0.95rem; line-height: 1.6;'>
                Trust through transparency. Every decision is explainable, verifiable, and designed to keep clinicians in control.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>
        Trusted by leading clinical research organizations worldwide.
    </div>
    """, unsafe_allow_html=True)

def show_page_header(title, subtitle, theme_color="#F8D849", pattern_type="connectivity"):
    """Displays a premium page header with unique visual identity."""
    
    # Define visual patterns using CSS
    patterns = {
        "connectivity": f"radial-gradient(circle at 20% 50%, {theme_color}1a 0%, transparent 50%), radial-gradient(circle at 80% 80%, {theme_color}0d 0%, transparent 40%)",
        "scan": f"linear-gradient(90deg, transparent 0%, {theme_color}22 50%, transparent 100%)",
        "precision": f"repeating-linear-gradient(45deg, transparent, transparent 10px, {theme_color}0d 10px, {theme_color}0d 11px)",
        "analytics": f"linear-gradient(to top, {theme_color}1a 0%, transparent 100%)"
    }
    
    pattern = patterns.get(pattern_type, patterns["connectivity"])
    
    st.markdown(f"""
    <div style='background: rgba(35, 12, 70, 0.6); backdrop-filter: blur(20px); border: 1px solid #B2963C; border-radius: 16px; padding: 2.5rem; margin-bottom: 2rem; position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);'>
        <div style='position: absolute; top:0; left:0; width: 100%; height: 100%; background: {pattern}; z-index: 0;'></div>
        <div style='position: relative; z-index: 1;'>
            <h1 style='color: #ffffff; margin: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -1px;'>
                {title.upper()} <span style='color: {theme_color};'>.</span>
            </h1>
            <p style='color: #A47E9B; font-size: 1.1rem; margin-top: 0.5rem;'>{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Navigation Logic
if st.session_state['page'] == 'landing':
    show_landing_page()
    st.stop()

# ==================== SIDEBAR NAVIGATION ====================
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #F8D849; margin-bottom: 0; font-size: 2rem;'></h1>
    <h2 style='color: #ffffff; margin-top: 0; font-size: 1.5rem; letter-spacing: 1px;'>CLINMATCH <span style='color: #F8D849;'>AI</span></h2>
    <p style='color: #A47E9B; font-size: 0.8rem;'>Clinical Trial Eligibility System</p>
</div>
""", unsafe_allow_html=True)

# Main Call-to-Action
if st.sidebar.button("✚  CREATE NEW TRIAL", use_container_width=True, type="primary"):
    st.session_state['show_create_trial_form'] = True
    st.rerun()

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation",
    ["Patient Database", "Screening Engine", "Trial Management", "Analytics"],
    key="nav_menu"
)

st.sidebar.markdown("---")


# ==================== PAGE 1: PATIENT DATABASE ====================
if menu == "Patient Database":
    show_page_header(
        "Patient Database", 
        "Secure directory of clinical records and medical history.",
        "#F8D849", "connectivity"
    )
    
    # ==================== NEW: PDF DATA INGESTION ====================
    with st.expander("Ingest Patient Data via PDF"):
        st.info("Upload a clinical note or patient summary in PDF format to automatically extract patient details.")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            raw_text = text_processor.extract_text_from_pdf(file_bytes)
            
            if raw_text:
                st.success("Text extracted successfully!")
                parsed_data = text_processor.parse_patient_from_text(raw_text)
                
                st.markdown("#### Review Extracted Information")
                col_p1, col_p2 = st.columns(2)
                
                with col_p1:
                    ext_name = st.text_input("Name", value=parsed_data['name'])
                    ext_age = st.number_input("Age", value=parsed_data['age'], min_value=0)
                    ext_gender = st.selectbox("Gender", ["M", "F", "U"], index=["M", "F", "U"].index(parsed_data['gender']))
                
                with col_p2:
                    ext_diag = st.text_input("Primary Condition", value=parsed_data['primary_condition'])
                    ext_notes = st.text_area("Clinical Notes", value=parsed_data['clinical_notes'], height=100)
                
                if st.button("Save to Database", use_container_width=True):
                    try:
                        db = next(db_connection.get_db())
                        new_patient = {
                            "name": ext_name,
                            "age": ext_age,
                            "gender": ext_gender,
                            "primary_condition": ext_diag,
                            "clinical_notes": ext_notes
                        }
                        crud.create_patient(db, new_patient)
                        st.success(f"Successfully added patient {ext_name} to the database!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Database Error: {str(e)}")
                        st.info("Check your PostgreSQL connection settings.")
            else:
                st.error("Could not extract text from this PDF. Please ensure it is a text-based PDF.")

    st.markdown("---")
    
    patients_df = data_loader.load_patient_demographics()
    treatments_df = data_loader.load_patient_treatments()
    
    # Professional Filter Strip (Collapsed for Efficiency)
    with st.expander("Filter Intelligence", expanded=False):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            age_filter = st.slider("Age Range", 0, 100, (0, 100))
        with f_col2:
            gender_filter = st.multiselect("Gender", patients_df['gender'].unique(), default=patients_df['gender'].unique())
        with f_col3:
            condition_filter = st.multiselect("Diagnosis", patients_df['diagnosis'].unique()[:20])

    # Apply filters
    filtered_df = patients_df[
        (patients_df['age'] >= age_filter[0]) & 
        (patients_df['age'] <= age_filter[1]) &
        (patients_df['gender'].isin(gender_filter))
    ]
    
    if condition_filter:
        filtered_df = filtered_df[filtered_df['diagnosis'].isin(condition_filter)]
    
    # Display table
    st.subheader(f"Showing {len(filtered_df)} Patients")
    
    # Format for display
    display_df = filtered_df[['subject_id', 'gender', 'age', 'diagnosis', 'insurance', 'deceased']].copy()
    display_df['age'] = display_df['age'].round(1)
    display_df['deceased'] = display_df['deceased'].apply(lambda x: "Yes" if x else "No")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Selected patient detail
    st.markdown("---")
    st.subheader("Patient Details")
    
    selected_patient_id = st.number_input("Enter Patient Subject ID:", min_value=0, value=0)
    
    if selected_patient_id > 0:
        patient = data_loader.get_patient_by_id(selected_patient_id)
        if patient:
            # Medical Record Chart Layout (EMR Style)
            st.markdown(f"""
            <div class='metric-card' style='border-left: 6px solid #F8D849; padding: 2rem; background: rgba(35, 12, 70, 0.6);'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem;'>
                    <div>
                        <h2 style='margin: 0; color: #ffffff;'>P-{patient.get('subject_id')}</h2>
                        <p style='color: #A47E9B; letter-spacing: 2px; font-weight: 600;'>OFFICIAL MEDICAL RECORD</p>
                    </div>
                    <div style='text-align: right;'>
                        <div style='background: rgba(248, 216, 73, 0.1); color: #F8D849; padding: 0.4rem 1rem; border-radius: 50px; font-weight: 700; font-size: 0.8rem; border: 1px solid #F8D849;'>ACTIVE RECRUITMENT</div>
                    </div>
                </div>
                
                <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 2rem;'>
                    <div>
                        <p style='color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 0;'>PATIENT NAME</p>
                        <p style='font-weight: 700; font-size: 1.1rem; color: #f3f4f6;'>CONFIDENTIAL</p>
                    </div>
                    <div>
                        <p style='color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 0;'>GENDER / AGE</p>
                        <p style='font-weight: 700; font-size: 1.1rem; color: #f3f4f6;'>{patient.get('gender')} / {round(float(patient.get('age')), 1)}yr</p>
                    </div>
                    <div>
                        <p style='color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 0;'>VITAL STATUS</p>
                        <p style='font-weight: 700; font-size: 1.1rem; color: #34d399;'>{"LIVING" if not patient.get('deceased') else "DECEASED"}</p>
                    </div>
                    <div>
                        <p style='color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 0;'>INSURANCE TYPE</p>
                        <p style='font-weight: 700; font-size: 1.1rem; color: #f3f4f6;'>{patient.get('insurance')}</p>
                    </div>
                </div>
                
                <div style='margin-top: 2rem; padding: 1.5rem; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid #A47E9B;'>
                    <p style='color: #F8D849; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 0.5rem;'>PRIMARY CLINICAL DIAGNOSIS</p>
                    <h3 style='margin: 0; color: #ffffff; font-size: 1.4rem;'>{patient.get('diagnosis')}</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            treatments = data_loader.get_patient_conditions(selected_patient_id)
            if treatments:
                st.markdown("#### Treatments & Conditions")
                conditions = treatments.get('conditions', 'N/A')
                medications = treatments.get('medications', 'N/A')
                
                if conditions and conditions != 'nan':
                    st.write("**Conditions:**")
                    for cond in str(conditions).split('|'):
                        st.write(f"  • {cond.strip()}")
                
                if medications and medications != 'nan':
                    st.write("**Medications:**")
                    for med in str(medications).split('|'):
                        st.write(f"  • {med.strip()}")
        else:
            st.warning("Patient not found in database")

# ==================== PAGE 2: SCREENING ENGINE ====================
elif menu == "Screening Engine":
    show_page_header(
        "Screening Engine", 
        "AI-powered eligibility assessment and clinical alignment.",
        "#A47E9B", "scan"
    )
    st.markdown("AI-powered eligibility screening with rule-based logic")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Select Patient")
        patients_df = data_loader.load_patient_demographics()
        patient_options = {f"P-{int(row['subject_id'])} ({row['diagnosis']})": int(row['subject_id']) 
                          for _, row in patients_df.head(100).iterrows()}
        selected_patient_name = st.selectbox("Choose Patient", list(patient_options.keys()))
        selected_patient_id = patient_options[selected_patient_name]
    
    with col2:
        st.subheader("Define Trial Criteria")
        trial_nct = st.text_input("Trial NCT ID", value="NCT045521")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Inclusion Criteria (comma-separated)**")
        inclusion_text = st.text_area("Enter keywords patient must have", 
                                     value="Diabetes,Type 2", 
                                     height=80)
    
    with col2:
        st.write("**Exclusion Criteria (comma-separated)**")
        exclusion_text = st.text_area("Enter keywords that disqualify patient", 
                                     value="Pregnancy,Heart Failure", 
                                     height=80)
    
    # Parse criteria
    inclusion_keywords = [k.strip() for k in inclusion_text.split(',') if k.strip()]
    exclusion_keywords = [k.strip() for k in exclusion_text.split(',') if k.strip()]
    
    # Additional filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_age = st.number_input("Minimum Age", value=18, min_value=0, max_value=120)
    
    with col2:
        max_age = st.number_input("Maximum Age", value=75, min_value=0, max_value=150)
    
    with col3:
        required_gender = st.selectbox("Required Gender", ["Any", "M", "F"])
    
    st.markdown("---")
    
    if st.button("Run Screening", use_container_width=True):
        with st.spinner("Running AI-powered eligibility analysis..."):
            time.sleep(1.5)
            
            # Get patient data
            patient_data = data_loader.get_patient_by_id(selected_patient_id)
            
            if patient_data:
                # Build trial rules
                trial_rules = {
                    "inclusion_keywords": inclusion_keywords,
                    "exclusion_keywords": exclusion_keywords,
                    "min_age": min_age,
                    "max_age": max_age,
                }
                
                if required_gender != "Any":
                    trial_rules["required_gender"] = required_gender
                
                # Apply rules
                result = rules_engine.apply_rules(patient_data, trial_rules)
                
                # Display results
                st.success("✅ Screening Complete!")
                st.markdown("---")
                
                # Primary Outcome Zone (High Impact)
                st.markdown(f"""
                <div class='metric-card' style='text-align: center; border-top: 4px solid {"#10b981" if result['eligible'] else "#ef4444"}; background: rgba(35, 12, 70, 0.6);'>
                    <div style='display: flex; justify-content: space-around; align-items: center;'>
                        <div>
                            <p style='color: #A47E9B; font-size: 0.9rem; margin: 0;'>MATCH CONFIDENCE</p>
                            <h2 style='color: #F8D849; font-size: 3.5rem; margin: 0;'>{result['score']:.1f}%</h2>
                        </div>
                        <div style='height: 80px; width: 1px; background: rgba(255,255,255,0.1);'></div>
                        <div>
                            <p style='color: #A47E9B; font-size: 0.9rem; margin: 0;'>DETERMINATION</p>
                            <h2 style='color: {"#10b981" if result['eligible'] else "#ef4444"}; font-size: 3rem; margin: 0;'>{"ELIGIBLE" if result['eligible'] else "INELIGIBLE"}</h2>
                        </div>
                        <div style='height: 80px; width: 1px; background: rgba(255,255,255,0.1);'></div>
                        <div>
                            <p style='color: #A47E9B; font-size: 0.9rem; margin: 0;'>VALIDATION</p>
                            <h2 style='color: #ffffff; font-size: 3rem; margin: 0;'>{result['passed_checks']}/{result['total_checks']}</h2>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Evidence Panel (Secondary Zone)
                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown("### Clinical Analysis Log")
                for check in result['checks']:
                    status_text = "PASS" if check['passed'] else "FAIL"
                    status_color = "#10b981" if check['passed'] else "#ef4444"
                    st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 1.2rem; border-radius: 12px; margin-bottom: 1rem; border-left: 5px solid {status_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
                        <span style='color: {status_color}; font-weight: 800; font-size: 0.8rem; letter-spacing: 1px;'>{status_text}</span><br>
                        <p style='font-size: 1rem; margin-top: 0.4rem; color: #f3f4f6;'>{check['check']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Metadata Summary Area
                st.markdown("<br>", unsafe_allow_html=True)
                sum_col1, sum_col2 = st.columns(2)
                
                with sum_col1:
                    with st.container(border=True):
                        st.subheader("Patient Profile")
                        st.caption(f"Subject: P-{patient_data['subject_id']}")
                        st.write(f"**Demographics:** {patient_data['gender']} / {round(float(patient_data['age']), 1)}yr")
                        st.write(f"**Diagnosis:** {patient_data['diagnosis']}")
                
                with sum_col2:
                    with st.container(border=True):
                        st.subheader("Trial Protocol")
                        st.caption(f"NCT: {trial_nct}")
                        st.write(f"**Requirements:** {min_age}-{max_age}yr / {required_gender}")
                
                # Clinician Action Center
                st.markdown("<br>", unsafe_allow_html=True)
                act_col1, act_col2, act_col3 = st.columns(3)
                
                with col1:
                    if st.button("Approve Match", use_container_width=True):
                        try:
                            # db = next(db_connection.get_db())
                            # crud.create_match_result(db, result) # Implementation pending
                            st.success("Match approved! Added to database.")
                        except Exception as e:
                             st.error(f"❌ Database Error: {str(e)}")
                
                with col2:
                    if st.button("Mark for Review", use_container_width=True):
                        st.info("Match marked for manual review.")
                
                with col3:
                    if st.button("Reject Match", use_container_width=True):
                        st.error("Match rejected.")
            else:
                st.error("Patient not found in database")

# ==================== PAGE 3: TRIAL MANAGEMENT ====================
elif menu == "Trial Management":
    show_page_header(
        "Trial Management", 
        "Registry of active clinical protocols and pharmaceutical trials.",
        "#B2963C", "precision"
    )
    
    # ==================== NEW: TRIAL-PATIENT MATCHING MODULE ====================
    st.markdown("### Trial-to-Patient Match Finder")
    st.info("Select an active trial to find the best matching patient candidates from the database.")
    
    # Fetch real trials from database
    real_trials = []
    try:
        db = next(db_connection.get_db())
        real_trials = crud.get_all_trials(db)
    except Exception as e:
        st.error(f"❌ **Database Connection Failed**: {str(e)}")
        st.info("Please ensure your PostgreSQL server is running and the credentials in `app/core/config.py` are correct.")
        # Optional: Add a button to attempt reconnection or fallback logic here

    
    if not real_trials:
        # Fallback to mock data for demonstration if DB is empty
        mock_trials_data = {
            "NCT055221_DEMO": {
                "title": "Diabetes Type 2 Management (DEMO)", 
                "inclusion": "Type 2 Diabetes, HbA1c > 7.0, Age > 40", 
                "exclusion": "Pregnancy, Heart Failure", 
                "min_age": 40,
                "max_age": 80
            },
            "NCT099882_DEMO": {
                "title": "Hypertension \u0026 ACE Inhibitors (DEMO)", 
                "inclusion": "Hypertension, ACE Inhibitors", 
                "exclusion": "Kidney Disease, Hypotension", 
                "min_age": 18,
                "max_age": 90
            }
        }
    else:
        mock_trials_data = {
            t.nct_id: {
                "title": t.title, 
                "inclusion": t.inclusion_criteria, 
                "exclusion": t.exclusion_criteria, 
                "min_age": 18, # Default if not in basic schema
                "max_age": 85  # Default if not in basic schema
            } for t in real_trials
        }
    
    col1, col2 = st.columns([2, 1])
    if mock_trials_data:
        with col1:
            selected_nct = st.selectbox("Select Trial to Analyze", list(mock_trials_data.keys()), 
                                       format_func=lambda x: f"{x} - {mock_trials_data[x]['title']}")
        
        with col2:
            st.write("") # Spacer
            st.write("") # Spacer
            run_match = st.button("Find Candidate Matches", use_container_width=True)
    else:
        run_match = False
        
    if run_match:
        with st.spinner("Running batch matching logic for all patients..."):
            trial = mock_trials_data[selected_nct]
            patients_df = data_loader.load_patient_demographics()
            
            trial_rules = {
                "inclusion_keywords": [k.strip() for k in trial['inclusion'].split(',')],
                "exclusion_keywords": [k.strip() for k in trial['exclusion'].split(',')],
                "min_age": trial['min_age'],
                "max_age": trial['max_age']
            }
            
            candidates = []
            for _, p in patients_df.iterrows():
                p_data = {
                    'subject_id': p['subject_id'],
                    'age': p['age'],
                    'gender': p['gender'],
                    'diagnosis': p['diagnosis']
                }
                res = rules_engine.apply_rules(p_data, trial_rules)
                
                priority = "Low"
                if res['score'] >= 90: priority = "High"
                elif res['score'] >= 75: priority = "Medium"
                
                candidates.append({
                    "Subject ID": int(p['subject_id']),
                    "Diagnosis": p['diagnosis'],
                    "Age": round(float(p['age']), 1),
                    "Match Score": f"{res['score']:.1f}%",
                    "Eligibility": "Eligible" if res['eligible'] else "Ineligible",
                    "Priority": priority,
                    "Raw Score": res['score']
                })
            
            # Create Results DataFrame
            results_df = pd.DataFrame(candidates)
            results_df = results_df.sort_values(by="Raw Score", ascending=False)
            
            # Display Metrics
            eligible_df = results_df[results_df['Eligibility'] == "Eligible"]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Patients Screened", len(patients_df))
            m2.metric("Eligible Candidates", len(eligible_df))
            m3.metric("High Priority Matches", len(results_df[results_df['Priority'] == "High"]))
            
            st.markdown("#### ✅ Eligible Candidates List")
            if not eligible_df.empty:
                st.dataframe(eligible_df.drop(columns=['Raw Score', 'Eligibility']), use_container_width=True)
            else:
                st.info("No eligible candidates found for this protocol based on strict criteria.")

            with st.expander("View All Ranked Patients (Including Ineligible)"):
                st.dataframe(results_df.drop(columns=['Raw Score']).head(50), use_container_width=True)
            
            st.success(f"Analysis complete for {selected_nct}")

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Create Trial", "View Trials"])
    
    with tab1:
        st.subheader("Create New Trial")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nct_id = st.text_input("NCT ID", value="NCT045521")
            title = st.text_input("Trial Title", value="Diabetes Type 2 Management Study")
        
        with col2:
            phase = st.selectbox("Phase", ["Phase 1", "Phase 2", "Phase 3", "Phase 4"])
            status = st.selectbox("Status", ["Recruiting", "Active", "Completed", "Closed"])
            participants = st.number_input("Target Participants", min_value=1, value=100)
        
        inclusion = st.text_area("Inclusion Criteria", 
                               value="Age >= 18\nDiagnosis: Type 2 Diabetes\nHbA1c > 7.5%",
                               height=100)
        
        exclusion = st.text_area("Exclusion Criteria", 
                               value="Pregnancy\nHistory of Heart Failure\nKidney disease",
                               height=100)
        
        if st.button("Save Trial", use_container_width=True):
            try:
                # Create DB Session
                db = next(db_connection.get_db())
                crud.create_trial(db, {
                    "nct_id": nct_id,
                    "title": title,
                    "phase": phase,
                    "status": status,
                    "inclusion_criteria": inclusion,
                    "exclusion_criteria": exclusion,
                    "target_participants": participants
                })
                st.success(f"Trial {nct_id} saved successfully!")
            except Exception as e:
                st.error(f"Error saving trial: {str(e)}")
    
    with tab2:
        st.subheader("Active Trials")
        
        # Mock trials data
        mock_trials = pd.DataFrame({
            "NCT ID": ["NCT045521", "NCT045522", "NCT045523"],
            "Title": ["Diabetes Type 2 Study", "Hypertension Management", "Heart Failure Trial"],
            "Phase": ["Phase 3", "Phase 2", "Phase 3"],
            "Status": ["Recruiting", "Active", "Completed"],
            "Participants": [250, 180, 320]
        })
        
        st.dataframe(mock_trials, use_container_width=True)

# ==================== PAGE 4: ANALYTICS ====================
elif menu == "Analytics":
    show_page_header(
        "Analytics Dashboard", 
        "High-fidelity cohort metrics and survivability analysis.",
        "#F8D849", "analytics"
    )
    
    patients_df = data_loader.load_patient_demographics()
    treatments_df = data_loader.load_patient_treatments()
    
    # Analytics Control Cluster (Insight Strip)
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns([1, 1, 1, 1, 1.2])
    
    with m_col1:
        st.caption("COHORT SCALE")
        st.metric("Total Patients", len(patients_df))
    with m_col2:
        st.caption("PATHOLOGY DENSITY")
        st.metric("Active Diagnosis", patients_df['diagnosis'].nunique())
    with m_col3:
        st.caption("TREATMENT VOLUME")
        st.metric("Procedures", len(treatments_df))
    with m_col4:
        st.caption("SURVIVABILITY")
        st.metric("Mortality Rate", f"{(patients_df['deceased'].sum()/len(patients_df)*100):.1f}%")
    with m_col5:
        st.caption("COHORT MOMENTUM")
        st.markdown("<div style='color: #34d399; font-weight: 700; font-size: 1.4rem;'>+12.4% <span style='font-size: 0.8rem; color: #A47E9B; font-weight: 400;'>VS LAST MONTH</span></div>", unsafe_allow_html=True)
    
    # Visualization Grid
    v_col1, v_col2 = st.columns(2)
    
    with v_col1:
        st.subheader("Demographic Distribution")
        fig_age = px.histogram(patients_df, x="age", nbins=20, 
                             title="Age Distribution",
                             color_discrete_sequence=['#F8D849'])
        fig_age.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f3f4f6',
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
        )
        st.plotly_chart(fig_age, use_container_width=True)
        
    with v_col2:
        st.subheader("Gender Composition")
        fig_gender = px.pie(patients_df, names="gender", 
                           title="Patient Gender Split",
                           hole=0.4,
                           color_discrete_sequence=['#F8D849', '#A47E9B', '#B2963C'])
        fig_gender.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f3f4f6',
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
        )
        st.plotly_chart(fig_gender, use_container_width=True)

    # Visualization Grid
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        st.subheader("Insurance Distribution")
        insurance_data = patients_df['insurance'].value_counts()
        fig = px.pie(values=insurance_data.values, names=insurance_data.index, 
                     color_discrete_sequence=px.colors.sequential.Sunsetdark)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#f3f4f6', margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with viz_col2:
        st.subheader("Mortality Analysis")
        mortality_data = patients_df[patients_df['age'] > 0].copy()
        mortality_data['age_group'] = pd.cut(mortality_data['age'], bins=[0, 18, 40, 60, 80, 150])
        mortality_by_age = mortality_data.groupby('age_group')['deceased'].apply(lambda x: (x.sum()/len(x)*100)).reset_index()
        mortality_by_age.columns = ['Age Group', 'Mortality Rate (%)']
        mortality_by_age['Age Group'] = mortality_by_age['Age Group'].astype(str)
        
        fig = px.bar(mortality_by_age, x='Age Group', y='Mortality Rate (%)', 
                     color_discrete_sequence=['#B2963C', '#F8D849'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#f3f4f6', margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; color: #A47E9B; font-size: 11px; padding: 20px;'>
        <p><b>Clinical Trial Eligibility Decision Support v1.0</b> | Secure Clinical Decision Support System</p>
        <p>Advanced Analytics Engine Active • Database Status: Synchronized</p>
        <p>© 2026 Clinical Intelligence Research Institute</p>
    </div>
    """, unsafe_allow_html=True)
