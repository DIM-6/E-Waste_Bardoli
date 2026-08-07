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

st.title("🏫 SURAT eWaste Survey - Data Form")
tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        rows, service, spreadsheet_id = get_sheet_data(tab_name)
        if len(rows) < 2:
            st.warning("Google Sheet માં ડેટા નથી!")
            return
            
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.columns = df.columns.str.strip()
        
        status_col = "Entry Status"
        ts_col = "TimeStamp"
        
        total = len(df)
        completed = len(df[df.get(status_col, "").astype(str).str.strip() == "Completed"]) if status_col in df.columns else 0
        
        # ડેશબોર્ડ
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
                <div style="text-align: center;"><div>કુલ શાળાઓ</div><div style="font-size: 18px; font-weight: bold;">{total}</div></div>
                <div style="text-align: center;"><div>એન્ટ્રી પૂર્ણ</div><div style="font-size: 18px; font-weight: bold; color: green;">{completed}</div></div>
                <div style="text-align: center;"><div>બાકી એન્ટ્રી</div><div style="font-size: 18px; font-weight: bold; color: red;">{total - completed}</div></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            code_cols = [c for c in df.columns if 'code' in c.lower() or 'sch' in c.lower()]
            if code_cols:
                c_col = code_cols[0]
                match = df[df[c_col].astype(str).str.strip() == str(school_code).strip()]
                
                if not match.empty:
                    idx = match.index[0]
                    row_data = match.iloc[0]
                    st.success("શાળાની માહિતી મળી ગઈ છે:")
                    
                    with st.form(key=f"form_{tab_name}"):
                        updated_inputs = {}
                        for col in df.columns:
                            if col in [status_col, ts_col]:
                                continue
                            val = str(row_data[col]) if pd.notna(row_data[col]) else ""
                            # પહેલી 5 કોલમ લોક રાખવી હોય તો
                            is_disabled = list(df.columns).index(col) <= 5
                            updated_inputs[col] = st.text_input(col, value=val, disabled=is_disabled)
                        
                        if st.form_submit_button("ફેરફાર સેવ કરો"):
                            with st.spinner('સેવ થઈ રહ્યું છે...'):
                                sheet_row_idx = idx + 2 # 헤ડર અને 0-index ના લીધે +2
                                
                                # અસલી રો નો ડેટા મેળવીને તેમાં જ ફેરફાર કરીએ જેથી કૉલમની સંખ્યા પરફેક્ટ મેચ થાય
                                current_row_values = rows[sheet_row_idx - 1]
                                
                                # જો શીટમાં કૉલમ ઓછી હોય તો તેને લંબાવી દઈએ
                                while len(current_row_values) < len(df.columns):
                                    current_row_values.append("")
                                    
                                for i, col in enumerate(df.columns):
                                    if col == status_col:
                                        current_row_values[i] = "Completed"
                                    elif col == ts_col:
                                        current_row_values[i] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    elif col in updated_inputs:
                                        current_row_values[i] = updated_inputs[col]
                                        
                                body = {'values': [current_row_values]}
                                service.spreadsheets().values().update(
                                    spreadsheetId=spreadsheet_id, 
                                    range=f"{tab_name}!A{sheet_row_idx}",
                                    valueInputOption="RAW", 
                                    body=body
                                ).execute()
                                
                                st.cache_data.clear()
                                st.success("માહિતી સફળતાપૂર્વક સેવ થઈ ગઈ છે!")
                                st.rerun()
                else:
                    st.error("આ કોડવાળી શાળા મળી નથી!")
            else:
                st.error("School Code વાળી કૉલમ મળી નથી!")
    except Exception as e:
        st.error(f"Error: {e}")

with tab1: handle_sheet("CAL")
with tab2: handle_sheet("Gyankunj")
