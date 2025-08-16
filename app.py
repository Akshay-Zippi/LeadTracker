import streamlit as st
import pandas as pd
import io
from db import get_all_leads, insert_lead, update_lead_status, delete_lead
from PIL import Image

# --- Page Config ---
st.set_page_config(page_title="Lead Tracker", layout="wide")

# --- Load Logo ---
logo_path = "logo2.png"
logo = Image.open(logo_path)

# --- CSS + Logo ---
st.markdown("""
    <style>
        .stApp { background-color: #40D0E0; }
        .logo { position: fixed; top: 10px; right: 50px; width: 120px; z-index: 100; }
    </style>
    <img src="file://logo1.png" class="logo">
""", unsafe_allow_html=True)
st.image(logo, width=120, use_container_width=False, output_format="PNG")

st.title("📕 Lead Tracker")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 All Leads", "➕ Add Lead", "📋 Manage Leads", "📂 Bulk Upload"])


# =====================================================
# TAB 1: ALL LEADS
# =====================================================
with tab1:
    st.subheader("All Leads")

    df_all = get_all_leads()
    if "first_contacted" in df_all.columns:
        df_all["first_contacted"] = pd.to_datetime(df_all["first_contacted"], errors="coerce")
    if "scheduled_walk_in" in df_all.columns:
        df_all["scheduled_walk_in"] = pd.to_datetime(df_all["scheduled_walk_in"], errors="coerce")

    # --- Filters ---
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        selected_status = st.selectbox("Status", ["All"] + df_all["status"].dropna().unique().tolist(), index=0)
    with col2:
        selected_source = st.selectbox("Source", ["All"] + df_all["source"].dropna().unique().tolist(), index=0)
    with col3:
        selected_licence = st.selectbox("Licence", ["All"] + df_all["licence"].dropna().unique().tolist(), index=0)
    with col4:
        first_contacted_date = st.date_input("First Contacted", value=None)
    with col5:
        walk_in_date = st.date_input("Scheduled Walk-in", value=None)

    # --- Apply Filters ---
    df_filtered = df_all.copy()
    if selected_status != "All":
        df_filtered = df_filtered[df_filtered["status"] == selected_status]
    if selected_source != "All":
        df_filtered = df_filtered[df_filtered["source"] == selected_source]
    if selected_licence != "All":
        df_filtered = df_filtered[df_filtered["licence"] == selected_licence]
    if first_contacted_date:
        df_filtered = df_filtered[df_filtered["first_contacted"].dt.date == first_contacted_date]
    if walk_in_date:
        df_filtered = df_filtered[df_filtered["scheduled_walk_in"].dt.date == walk_in_date]

    # --- Display ---
    if not df_filtered.empty:
        st.dataframe(df_filtered, use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Leads')
        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name="leads.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No leads match the filters.")


# =====================================================
# TAB 2: ADD LEAD
# =====================================================
with tab2:
    st.subheader("Add New Lead")
    name = st.text_input("Name")
    contact = st.text_input("Contact Number")
    address = st.text_area("Address")
    source = st.selectbox("Source", ["Instagram", "Referral", "Walk-in", "Other"])
    status = st.selectbox("Status", ["pending", "processing", "onboarded", "rejected"])
    first_contacted = st.date_input("First Contacted", value=None)
    notes = st.text_area("Notes")

    licence = st.selectbox("Licence", ["yes", "no"])
    scheduled_walk_in = st.date_input("Scheduled Walk-in", value=None)

    if st.button("Save Lead"):
        if name and contact:
            insert_lead(
                name, contact, address, source, status,
                first_contacted, notes, licence, scheduled_walk_in
            )
            st.success("✅ Lead Added Successfully!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("⚠️ Name & Contact are required.")


# =====================================================
# TAB 3: MANAGE LEADS
# =====================================================
with tab3:
    st.subheader("Manage Leads")
    df = get_all_leads()

    if "first_contacted" in df.columns:
        df["first_contacted"] = pd.to_datetime(df["first_contacted"], errors="coerce")
    if "scheduled_walk_in" in df.columns:
        df["scheduled_walk_in"] = pd.to_datetime(df["scheduled_walk_in"], errors="coerce")

    # --- Filters ---
    col1, col2, col3 = st.columns([1.5, 1.5, 2])
    with col1:
        selected_status = st.selectbox("Status", ["All"] + df["status"].dropna().unique().tolist(), index=0, key="manage_status")
    with col2:
        selected_source = st.selectbox("Source", ["All"] + df["source"].dropna().unique().tolist(), index=0, key="manage_source")
    with col3:
        search_term = st.text_input("Search", key="manage_search")

    df_filtered = df.copy()
    if selected_status != "All":
        df_filtered = df_filtered[df_filtered["status"] == selected_status]
    if selected_source != "All":
        df_filtered = df_filtered[df_filtered["source"] == selected_source]
    if search_term:
        df_filtered = df_filtered[
            df_filtered["name"].str.contains(search_term, case=False, na=False) |
            df_filtered["contact_number"].astype(str).str.contains(search_term, case=False, na=False)
        ]

    # --- Display Rows ---
    if not df_filtered.empty:
        for _, row in df_filtered.iterrows():
            cols = st.columns([1.2,1.2,1.2,1.2,1.2,1.2,1.5,1.5,2,0.8,0.8])
            with cols[0]:
                new_name = st.text_input(f"Name ({row['id']})", value=row["name"], key=f"name_{row['id']}")
            with cols[1]:
                new_contact = st.text_input(f"Contact ({row['id']})", value=row["contact_number"], key=f"contact_{row['id']}")
            with cols[2]:
                new_source = st.selectbox(f"Source ({row['id']})",
                                          ["Instagram","Referral","Walk-in","Other"],
                                          index=["Instagram","Referral","Walk-in","Other"].index(row["source"]) if row["source"] in ["Instagram","Referral","Walk-in","Other"] else 0,
                                          key=f"source_{row['id']}")
            with cols[3]:
                new_status = st.selectbox(f"Status ({row['id']})",
                                          ["pending","processing","onboarded","rejected"],
                                          index=["pending","processing","onboarded","rejected"].index(row["status"]) if row["status"] in ["pending","processing","onboarded","rejected"] else 0,
                                          key=f"status_{row['id']}")
            with cols[4]:
                new_first_contacted = st.date_input(f"First Contacted ({row['id']})",
                    value=row["first_contacted"].date() if pd.notnull(row["first_contacted"]) else pd.to_datetime("today").date(),
                    key=f"first_contacted_{row['id']}")
            with cols[5]:
                new_licence = st.selectbox(f"Licence ({row['id']})", ["yes","no"],
                                           index=["yes","no"].index(row["licence"]) if row["licence"] in ["yes","no"] else 1,
                                           key=f"licence_{row['id']}")
            with cols[6]:
                new_walk_in = st.date_input(f"Scheduled Walk-in ({row['id']})",
                    value=row["scheduled_walk_in"].date() if pd.notnull(row["scheduled_walk_in"]) else None,
                    key=f"walkin_{row['id']}")
            with cols[7]:
                new_notes = st.text_input(f"Notes ({row['id']})", value=row.get("notes",""), key=f"notes_{row['id']}")

            with cols[8]:
                if st.button("✅", key=f"update_{row['id']}"):
                    update_lead_status(
                        lead_id=row['id'],
                        name=new_name,
                        contact_number=new_contact,
                        source=new_source,
                        status=new_status,
                        first_contacted=pd.to_datetime(new_first_contacted),
                        notes=new_notes,
                        licence=new_licence,
                        scheduled_walk_in=pd.to_datetime(new_walk_in) if new_walk_in else None
                    )
                    st.success(f"Lead {new_name} updated!")
                    st.rerun()

            with cols[9]:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    delete_lead(row['id'])
                    st.success(f"Lead {row['name']} deleted!")
                    st.rerun()
    else:
        st.info("No leads found.")


# =====================================================
# TAB 4: BULK UPLOAD
# =====================================================
with tab4:
    st.subheader("📂 Bulk Upload Leads")

    # Template
    template_df = pd.DataFrame(columns=[
        "name","contact_number","address","source","status","first_contacted","notes","licence","scheduled_walk_in"
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Leads_Template')
    st.download_button("📥 Download Excel Template", output.getvalue(), "lead_upload_template.xlsx")

    # Upload
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv","xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        # Validation
        valid_status = ["pending","processing","onboarded","rejected"]
        valid_source = ["Instagram","Referral","Walk-in","Other"]
        valid_licence = ["yes","no"]

        df_upload["is_valid"] = True
        df_upload["errors"] = ""

        for idx, row in df_upload.iterrows():
            errors = []
            if pd.isna(row.get("name")) or pd.isna(row.get("contact_number")):
                errors.append("Missing name/contact")
            if row.get("status") not in valid_status:
                errors.append("Invalid status")
            if row.get("source") not in valid_source:
                errors.append("Invalid source")
            if row.get("licence") not in valid_licence:
                errors.append("Invalid licence")
            if errors:
                df_upload.at[idx, "is_valid"] = False
                df_upload.at[idx, "errors"] = ", ".join(errors)

        st.markdown("#### Preview Uploaded Leads")
        st.dataframe(df_upload)

        if st.button("✅ Insert Valid Leads"):
            valid_rows = df_upload[df_upload["is_valid"]]
            for _, row in valid_rows.iterrows():
                insert_lead(
                    row["name"],
                    row["contact_number"],
                    row.get("address",""),
                    row.get("source",""),
                    row.get("status","pending"),
                    row.get("first_contacted"),
                    row.get("notes",""),
                    row.get("licence","no"),
                    row.get("scheduled_walk_in")
                )
            st.success(f"{len(valid_rows)} leads inserted successfully!")