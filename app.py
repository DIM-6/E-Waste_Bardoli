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
    
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1:ZZ1000").execute()
    return result.get('values', []), service, spreadsheet_id

st.title("🏫 SURAT eWaste Survey - Data Form")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        rows, service, spreadsheet_id = get_sheet_data(tab_name)
        if len(rows) < 2:
            st.warning("Google Sheet માં ડેટા નથી!")
            return
            
        header = [str(c).strip() for c in rows[0] if str(c).strip() != ""]
        num_cols = len(header)
        
        data_rows = []
        for r in rows[1:]:
            while len(r) < num_cols: r.append("")
            data_rows.append(r[:num_cols])
            
        df = pd.DataFrame(data_rows, columns=header)
        
        status_col = header[-2]
        ts_col = header[-1]
        
        total = len(df)
        completed = len(df[df.get(status_col, "").astype(str).str.strip() == "Completed"]) if status_col in df else 0
        
        # ડેશબોર્ડ
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
                <div style="text-align: center;"><div>કુલ</div><div style="font-size: 18px; font-weight: bold;">{total}</div></div>
                <div style="text-align: center;"><div>પૂર્ણ</div><div style="font-size: 18px; font-weight: bold; color: green;">{completed}</div></div>
                <div style="text-align: center;"><div>બાકી</div><div style="font-size: 18px; font-weight: bold; color: red;">{total - completed}</div></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            code_cols = [c for c in df.columns if 'code' in c.lower() or 'sch' in c.lower()]
            if code_cols:
                match = df[df[code_cols[0]].astype(str).str.strip() == str(school_code).strip()]
                
                if not match.empty:
                    idx = match.index[0]
                    row_data = match.iloc[0]
                    st.success("શાળાની માહિતી મળી ગઈ છે:")
                    
                    with st.form(key=f"form_{tab_name}"):
                        updated_inputs = {}
                        for i, col in enumerate(header):
                            # જે ડેટા શીટમાં છે તે જ અહીં દેખાશે (જો ખાલી હશે તો ખાલી દેખાશે)
                            val = str(row_data[col]) if col in row_data else ""
                            
                            # પહેલી 5 કૉલમ Disable, છેલ્લી 2 કૉલમ પણ Disable (માત્ર વાંચવા માટે)
                            is_disabled = (i <= 5) or (i >= num_cols - 2)
                            updated_inputs[col] = st.text_input(col, value=val, disabled=is_disabled)
                        
                        if st.form_submit_button("ફેરફાર સેવ કરો"):
                            with st.spinner('સેવ થઈ રહ્યું છે...'):
                                sheet_row_idx = idx + 2 
                                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                final_values = []
                                for i, col_name in enumerate(header):
                                    if i == num_cols - 2:  # Entry Status
                                        final_values.append("Completed")
                                    elif i == num_cols - 1: # TimeStamp
                                        final_values.append(current_time)
                                    else:
                                        # બાકીની કૉલમ્સમાં જે છે તે જ રહેશે
                                        val = updated_inputs.get(col_name, row_data.get(col_name, ""))
                                        final_values.append(str(val))
                                
                                service.spreadsheets().values().update(
                                    spreadsheetId=spreadsheet_id, range=f"{tab_name}!A{sheet_row_idx}",
                                    valueInputOption="RAW", body={'values': [final_values[:num_cols]]}
                                ).execute()
                                
                                st.cache_data.clear()
                                st.success("માહિતી સેવ થઈ ગઈ છે!")
                                st.rerun()
                else:
                    st.error("શાળા મળી નથી!")
    except Exception as e:
        st.error(f"Error: {e}")

with tab1: handle_sheet("CAL")
with tab2: handle_sheet("Gyankunj")
