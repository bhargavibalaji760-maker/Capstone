# ClinMatch AI - Clinical Trial Eligibility Decision Support System

## 🏥 Project Overview
**ClinMatch AI** is an intelligent clinical trial eligibility decision support system. It automates patient-trial matching using AI and rule-based logic to improve consistency and provide transparent, clinician-validated eligibility decisions.

---

## 🚀 Workflow & Execution

### � Option 1: Using Docker (Recommended)
This is the fastest way to deploy the entire stack (Database, Backend, and Frontend).

1. **Start all services**:
   ```bash
   docker-compose up --build
   ```
2. **Access the application**:
   - **Main Dashboard**: [http://localhost:8501](http://localhost:8501)
   - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 💻 Option 2: Local Setup (Manual)
Use this if you want to run the services individually.

#### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

#### 2. Run the FastAPI Backend
In a separate terminal:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

#### 3. Run the Streamlit Dashboard
In another terminal:
```bash
cd frontend
python -m streamlit run streamlit_app.py
```

---

## 📖 Application Guide

### Dashboard Features
- **Patient Database**: Browse and filter 2,800+ real clinical records.
- **Screening Engine**: Run AI eligibility assessments against trial criteria.
- **Trial Management**: Create and manage clinical study protocols.
- **Analytics**: Visualize system-wide recruitment trends and patient data.

### � API Integration
- **Base URL**: `http://localhost:8000/api`
- **Key Endpoints**:
  - `/patients/`: Manage patient clinical data.
  - `/trials/`: Access trial protocol registry.
  - `/run_screening/`: Execute matching logic between patients and trials.

---

**Last Updated:** February 12, 2026
**Version:** 1.0.0
**Status:** ✅ Ready for Capstone Submission
