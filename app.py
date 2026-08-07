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
st.warning("⚠️ **સૂચના:** હાલ આ સાઇટ પર કામ ચાલી રહ્યું છે, જેથી હમણાં કોઈ પણ જાતની એન્ટ્રી કરવી નહીં.")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        rows, service, spreadsheet_id = get_sheet_data(tab_name)
        if len(rows) < 2:
            st.warning("Google Sheet માં કોઈ ડેટા નથી!")
            return
            
        header = [str(c).strip() for c in rows[0] if str(c).strip() != ""]
        num_cols = len(header)
        
        data_rows = []
        for r in rows[1:]:
            while len(r) < num_cols:
                r.append("")
            data_rows.append(r[:num_cols])
            
        df = pd.DataFrame(data_rows, columns=header)
        
        status_col = header[-2]
        ts_col = header[-1]
        
        total = len(df)
        completed = len(df[df.get(status_col, "").astype(str).str.strip() == "Completed"]) if status_col in df else 0
        
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
                    st.success("શાળાની માહિતી મળી ગઈ છે. નીચે બધી જ વિગતો ભરો:")
                    
                    with st.form(key=f"form_{tab_name}"):
                        updated_inputs = {}
                        
                        for i, col in enumerate(header):
                            val = str(row_data[col]) if col in row_data and pd.notna(row_data[col]) else ""
                            is_disabled = (i <= 5) or (i >= num_cols - 2)
                            
                            # જો અગાઉથી કઈ ભરેલું ન હોય તો છેલ્લી બે કૉલમ ખાલી જ દેખાશે (બાય ડિફોલ્ટ Completed નહીં આવે)
                            if i >= num_cols - 2 and (val == "nan" or val is None):
                                val = ""
                                
                            updated_inputs[col] = st.text_input(col, value=val, disabled=is_disabled)
                        
                        if st.form_submit_button("ફેરફાર સેવ કરો"):
                            with st.spinner('માહિતી સેવ થઈ રહી છે...'):
                                sheet_row_idx = idx + 2 
                                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                final_values = []
                                for i, col_name in enumerate(header):
                                    if i == num_cols - 2:  # Entry Status -> ફક્ત સેવ કરતી વખતે જ Completed થશે
                                        final_values.append("Completed")
                                    elif i == num_cols - 1: # TimeStamp -> ફક્ત સેવ કરતી વખતે જ સમય આવશે
                                        final_values.append(current_time)
                                    else:
                                        val = updated_inputs.get(col_name, row_data.get(col_name, ""))
                                        final_values.append(str(val))
                                        
                                final_values = final_values[:num_cols]
                                
                                body = {'values': [final_values]}
                                service.spreadsheets().values().update(
                                    spreadsheetId=spreadsheet_id, 
                                    range=f"{tab_name}!A{sheet_row_idx}",
                                    valueInputOption="RAW", 
                                    body=body
                                ).execute()
                                
                                st.cache_data.clear()
                                st.success(f"માહિતી સફળતાપૂર્વક સેવ થઈ ગઈ છે! (Time: {current_time})")
                                st.rerun()
                else:
                    st.error("આ કોડવાળી શાળા મળી નથી!")
            else:
                st.error("School Code વાળી કૉલમ મળી નથી!")
    except Exception as e:
        st.error(f"કનેક્શન કે ડેટામાં ભૂલ છે: {e}")

with tab1: handle_sheet("CAL")
with tab2: handle_sheet("Gyankunj")
