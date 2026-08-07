import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Google Sheets API કનેક્શન
@st.cache_data(ttl=600)
def get_sheet_data(sheet_name):
    creds_dict = dict(st.secrets["gcp"])
    if '\\n' in creds_dict['private_key']:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = "1oAeqzK2zgifwn--u2jjYicfmlhpvqhwNAXi1ErMfrIQ"
    
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:Z"
    ).execute()
    
    rows = result.get('values', [])
    return rows, service, spreadsheet_id, sheet_name

st.title("🏫 SURAT eWaste Survey - Data Form")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

if 'original_df_cache' not in st.session_state:
    st.session_state['original_df_cache'] = {}

def handle_sheet(tab_name):
    try:
        rows, service, spreadsheet_id, range_name = get_sheet_data(tab_name)
        if len(rows) < 2:
            st.warning("Google Sheet માં ડેટા નથી!")
            return
            
        current_df = pd.DataFrame(rows[1:], columns=rows[0])
        current_df.columns = current_df.columns.str.strip()

        # "Status" અને "Timestamp" કોલમ હોય તો તે ચેક કરો, નહીતર મેન્યુઅલ લોજિક
        status_col = "Status"
        ts_col = "Timestamp"
        
        # એન્ટ્રી પૂર્ણ ગણવા માટેનું લોજિક: Status == 'Completed'
        completed_entries = len(current_df[current_df.get(status_col, "") == "Completed"])
        total_schools = len(current_df)
        pending_entries = total_schools - completed_entries

        # --- ડેશબોર્ડ ---
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
                <div style="text-align: center;"><div>કુલ શાળાઓ</div><div style="font-size: 20px; font-weight: bold;">{total_schools}</div></div>
                <div style="text-align: center;"><div>એન્ટ્રી પૂર્ણ</div><div style="font-size: 20px; font-weight: bold; color: green;">{completed_entries}</div></div>
                <div style="text-align: center;"><div>બાકી એન્ટ્રી</div><div style="font-size: 20px; font-weight: bold; color: red;">{pending_entries}</div></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            code_col = [c for c in current_df.columns if 'code' in c.lower() or 'sch' in c.lower()][0]
            match_indices = current_df[current_df[code_col].astype(str).str.strip() == str(school_code).strip()].index
            
            if not match_indices.empty:
                row_idx = match_indices[0]
                current_school_row = current_df.iloc[row_idx]
                
                with st.form(key=f"form_{tab_name}"):
                    updated_data = {}
                    cols_list = list(current_df.columns)
                    
                    for col in cols_list:
                        val = str(current_school_row[col])
                        if col in [status_col, ts_col]: continue # આ કોલમ ફોર્મમાં નહી દેખાય
                        updated_data[col] = st.text_input(col, value=val, disabled=(cols_list.index(col) <= 5))
                    
                    if st.form_submit_button("ફેરફાર સેવ કરો"):
                        with st.spinner('સેવ થઈ રહ્યું છે...'):
                            sheet_row_idx = row_idx + 2
                            # સ્ટેટસ અને ટાઈમસ્ટેમ્પ અપડેટ
                            new_values = [updated_data[col] for col in cols_list]
                            
                            # Status અને Timestamp કોલમનું ઇન્ડેક્સ શોધી તેમાં વેલ્યુ મૂકો
                            if status_col in cols_list: new_values[cols_list.index(status_col)] = "Completed"
                            if ts_col in cols_list: new_values[cols_list.index(ts_col)] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            service.spreadsheets().values().update(
                                spreadsheetId=spreadsheet_id, range=f"{tab_name}!A{sheet_row_idx}",
                                valueInputOption="RAW", body={'values': [new_values]}
                            ).execute()
                            st.success("સફળતાપૂર્વક પૂર્ણ થયું!")
                            st.rerun()
            else:
                st.error("શાળા મળી નથી!")
                
    except Exception as e:
        st.error(f"Error: {e}")

with tab1: handle_sheet("CAL")
with tab2: handle_sheet("Gyankunj")
