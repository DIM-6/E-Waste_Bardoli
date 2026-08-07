import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

@st.cache_data(ttl=600)
def get_sheet_data(sheet_name):
    creds_dict = dict(st.secrets["gcp"])
    if '\\n' in creds_dict['private_key']:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = "1oAeqzK2zgifwn--u2jjYicfmlhpvqhwNAXi1ErMfrIQ"
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:Z").execute()
    return result.get('values', []), service, spreadsheet_id

st.title("🏫 SURAT eWaste Survey")
tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        rows, service, spreadsheet_id = get_sheet_data(tab_name)
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.columns = df.columns.str.strip()
        
        # Dashboard
        status_col, ts_col = "Entry Status", "TimeStamp"
        total = len(df)
        completed = len(df[df.get(status_col, "") == "Completed"])
        st.markdown(f"**કુલ: {total} | પૂર્ણ: {completed} | બાકી: {total - completed}**")
        
        school_code = st.text_input(f"School Code ({tab_name})")
        if school_code:
            match = df[df.iloc[:, 0].astype(str).str.strip() == school_code.strip()]
            if not match.empty:
                idx = match.index[0]
                row_data = match.iloc[0]
                
                with st.form("edit_form"):
                    updated_row = row_data.copy()
                    for col in df.columns:
                        if col in [status_col, ts_col]: continue
                        
                        # લોક કરેલી કૉલમ્સ (પહેલી 6)
                        if list(df.columns).index(col) <= 5:
                            st.write(f"**{col}:** {row_data[col]}")
                        else:
                            updated_row[col] = st.text_input(col, value=row_data[col])
                    
                    if st.form_submit_button("સેવ કરો"):
                        updated_row[status_col] = "Completed"
                        updated_row[ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # બધી જ ૨૪ કૉલમનો ડેટા લિસ્ટમાં કન્વર્ટ કરો
                        new_values = [str(updated_row[c]) for c in df.columns]
                        
                        service.spreadsheets().values().update(
                            spreadsheetId=spreadsheet_id, range=f"{tab_name}!A{idx + 2}",
                            valueInputOption="RAW", body={'values': [new_values]}
                        ).execute()
                        st.success("સેવ થઈ ગયું!")
                        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

with tab1: handle_sheet("CAL")
with tab2: handle_sheet("Gyankunj")
