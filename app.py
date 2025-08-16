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

# --- CSS for background & positioning ---
st.markdown("""
    <style>
        .stApp {
            background-color: #40D0E0;
        }
        .logo {
            position: fixed;
            top: 10px;
            right: 50px;
            width: 120px;
            z-index: 100;
        }
    </style>
    <img src="file://logo1.png" class="logo">
""", unsafe_allow_html=True)

# --- Display logo ---
st.image(logo, width=120, use_container_width =False, output_format="PNG")

st.set_page_config(page_title="Lead Tracker", layout="wide")

st.title("📕 Lead Tracker")

tab1, tab2, tab3, tab4 = st.tabs(["📊 All Leads", "➕ Add Lead", "📋 Manage Leads", "📂 Bulk Upload"])

# --- Tab 1: All Leads ---
with tab1:
    st.markdown("""
            <style>
            /* Target only the container that holds tab1's content */
            div[data-testid="stVerticalBlock"] > div:nth-of-type(4) {
                background-color: rgba(100, 143, 137, 0.5) !important;
                padding: 20px;
                border-radius: 10px;
            }
            </style>
        """, unsafe_allow_html=True)

    st.subheader("All Leads")

    df_all = get_all_leads()
    if "first_contacted" in df_all.columns:
        df_all["first_contacted"] = pd.to_datetime(df_all["first_contacted"], errors="coerce")

    # Filters in single line
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        selected_status = st.selectbox("Status", ["All"] + df_all["status"].dropna().unique().tolist(), index=0, key="filter_status")
    with col2:
        selected_source = st.selectbox("Source", ["All"] + df_all["source"].dropna().unique().tolist(), index=0, key="filter_source")
    with col3:
        selected_first_contacted = st.date_input("First Contacted", value=None, key="filter_first_contacted")

    # Apply filters
    df_filtered = df_all.copy()
    if selected_status != "All":
        df_filtered = df_filtered[df_filtered["status"] == selected_status]
    if selected_source != "All":
        df_filtered = df_filtered[df_filtered["source"] == selected_source]
    if selected_first_contacted:
        df_filtered = df_filtered[df_filtered["first_contacted"].dt.date == selected_first_contacted]

    # Display table
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

    st.markdown("</div>", unsafe_allow_html=True)



# --- Tab 2: Add Lead ---
with tab2:
    st.subheader("Add New Lead")
    name = st.text_input("Name")
    contact = st.text_input("Contact Number")
    address = st.text_area("Address")
    source = st.selectbox("Source", ["Instagram", "Referral", "Walk-in", "Other"])
    status = st.selectbox("Status", ["pending", "processing", "onboarded", "rejected"])
    first_contacted = st.date_input("First Contacted", value=None)
    next_update = st.date_input("Next Update", value=first_contacted )
    notes = st.text_area("Notes")
    # If next_update is same as first_contacted, store None
    if next_update == first_contacted:
        next_update = None

    if st.button("Save Lead"):
        if name and contact:
            insert_lead(name, contact, address, source, status,first_contacted, notes)
            st.success("✅ Lead Added Successfully!")
            # Clear cached leads so All Leads tab reloads
            st.cache_data.clear()

            # Force page refresh
            st.rerun()
        else:
            st.warning("⚠️ Name & Contact are required.")

# --- Tab 3: Manage Leads ---
with tab3:
    st.markdown("""
                <style>
                /* Target only the container that holds tab1's content */
                div[data-testid="stVerticalBlock"] > div:nth-of-type(4) {
                    background-color: rgba(100, 143, 137, 0.5) !important;
                    padding: 20px;
                    border-radius: 10px;
                }
                </style>
            """, unsafe_allow_html=True)

    st.subheader("Manage Leads")
    df = get_all_leads()

    if "first_contacted" in df.columns:
        df["first_contacted"] = pd.to_datetime(df["first_contacted"], errors="coerce")

    # --- Compact Filters ---
    st.markdown("### Filters")
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 2, 2])

    with col1:
        selected_status = st.selectbox("Status", ["All"] + df["status"].dropna().unique().tolist(), index=0, key="manage_status")

    with col2:
        selected_source = st.selectbox("Source", ["All"] + df["source"].dropna().unique().tolist(), index=0, key="manage_source")

    with col3:
        search_term = st.text_input("Search", key="manage_search")

    with col4:
        if "first_contacted" in df.columns and not df["first_contacted"].dropna().empty:
            min_date = df["first_contacted"].dropna().min().date()
            max_date = df["first_contacted"].dropna().max().date()
            date_filter = st.date_input(
                "Date Between",
                (min_date, max_date),
                key="manage_date"

            )

        else:
            date_filter = None

    # --- Apply Filters ---
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
    if date_filter and len(date_filter) == 2:
        start_date, end_date = date_filter
        df_filtered = df_filtered[
            (df_filtered["first_contacted"] >= pd.to_datetime(start_date)) &
            (df_filtered["first_contacted"] <= pd.to_datetime(end_date))
        ]

    # --- Display Leads with Update/Delete ---
    if not df_filtered.empty:
        for index, row in df_filtered.iterrows():
            cols = st.columns([1.5, 1.5, 1.2, 1.2, 1.5, 2, 0.8, 0.8])
            with cols[0]:
                new_name = st.text_input(
                    f"Name ({row['id']})",
                    value=row["name"],
                    key=f"name_{row['id']}"
                )
            with cols[1]:
                new_contact = st.text_input(
                    f"Contact Number ({row['id']})",
                    value=row["contact_number"],
                    key=f"contact_{row['id']}"
                )
            with cols[2]:
                new_source = st.selectbox(
                    f"Source ({row['id']})",
                    ["Instagram", "Referral", "Walk-in", "Other"],
                    index=["Instagram", "Referral", "Walk-in", "Other"].index(row["source"]) if row["source"] in ["Instagram", "Referral", "Walk-in", "Other"] else 0,
                    key=f"source_{row['id']}"
                )
            with cols[3]:
                new_status = st.selectbox(
                    f"Status ({row['id']})",
                    ["pending", "processing", "onboarded", "rejected"],
                    index=["pending", "processing", "onboarded", "rejected"].index(row["status"]),
                    key=f"status_{row['id']}"
                )
            with cols[4]:
                new_first_contacted = st.date_input(
                    f"First Contacted ({row['id']})",
                    value=row["first_contacted"].date() if pd.notnull(row["first_contacted"]) else pd.to_datetime("today").date(),
                    key=f"first_contacted_{row['id']}"
                )
            with cols[5]:
                new_notes = st.text_input(
                    f"Notes ({row['id']})",
                    value=row.get("notes", ""),
                    key=f"notes_{row['id']}"
                )
            with cols[6]:
                if st.button("✅", key=f"update_{row['id']}"):
                    update_lead_status(
                        row['id'],
                        new_status,
                        new_notes,
                        new_name,
                        new_contact,
                        new_source,
                        new_first_contacted
                    )
                    st.success(f"Lead {new_name} updated!")
                    st.rerun()
            with cols[7]:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    delete_lead(row['id'])
                    st.success(f"Lead {row['name']} deleted!")

    else:
        st.info("No leads match your filters.")

# --- Tab 4: Bulk Upload ---
with tab4:
    st.markdown("### 📂 Bulk Upload Leads")

    # Download template
    template_df = pd.DataFrame(columns=["name", "contact_number", "address", "source", "status","first_contacted", "notes"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Leads_Template')
    st.download_button(
        label="Download Excel Template",
        data=output.getvalue(),
        file_name="lead_upload_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
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
        valid_status = ["pending", "processing", "onboarded", "rejected"]
        valid_source = ["Instagram", "Referral", "Walk-in", "Other"]
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
            if errors:
                df_upload.at[idx, "is_valid"] = False
                df_upload.at[idx, "errors"] = ", ".join(errors)

        st.markdown("#### Preview Uploaded Leads")
        st.dataframe(df_upload)

        if st.button("✅ Insert Valid Leads"):
            valid_rows = df_upload[df_upload["is_valid"]]
            invalid_rows = df_upload[~df_upload["is_valid"]]

            for _, row in valid_rows.iterrows():
                insert_lead(
                    row["name"],
                    row["contact_number"],
                    row.get("address", ""),
                    row.get("source", ""),
                    row.get("status", "pending"),
                    row.get("notes", "")
                )


            st.success(f"{len(valid_rows)} leads inserted successfully!")
            if not invalid_rows.empty:
                st.warning(f"{len(invalid_rows)} rows failed validation. Check 'errors' column above.")
