import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets કનેક્શન સેટઅપ
def get_sheet(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp"])
    if '\\n' in creds_dict['private_key']:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_url('https://docs.google.com/spreadsheets/d/1oAeqzK2zgifwn--u2jjYicfmlhpvqhwNAXi1ErMfrIQ/edit').worksheet(sheet_name)

st.title("🏫 SURAT eWaste Survey")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        sheet = get_sheet(tab_name)
        
        # આખી શીટનો ડેટા રો અને કોલમ મુજબ મેળવીએ છીએ
        rows = sheet.get_all_values()
        if len(rows) < 2:
            st.warning("Google Sheet માં કોઈ ડેટા નથી!")
            return
            
        # પહેલી રો ને હેડર અને બાકીના ડેટાને DataFrame બનાવીએ છીએ
        df = pd.DataFrame(rows[1:], columns=rows[0])
        
        # કોલમ્સના નામની આસપાસની સ્પેસ સાફ કરીએ
        df.columns = df.columns.str.strip()
        
        # સ્ક્રીન પર ચેક કરવા માટે કે કયા કોલમ્સ મળ્યા
        st.write(" ઉપલબ્ધ કોલમ્સ:", list(df.columns))

        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            # કોડ વાળી કોલમ શોધીએ
            code_col = [c for c in df.columns if 'code' in c.lower() or 'sch' in c.lower()]
            
            if code_col:
                actual_code_col = code_col[0]
                # ડેટા મેચ કરીએ
                record = df[df[actual_code_col].astype(str).str.strip() == str(school_code).strip()]
                
                if not record.empty:
                    name_col = [c for c in df.columns if 'name' in c.lower()]
                    school_name = record.iloc[0][name_col[0]] if name_col else "નામ મળ્યું નથી"
                    
                    st.success(f"શાળાનું નામ: {school_name}")
                    
                    status = st.selectbox("Status", ["Pending", "Completed"], key=f"sel_{tab_name}")
                    
                    if st.button("સેવ કરો", key=f"btn_{tab_name}VAL"):
                        # રો ઇન્ડેક્સ શોધીને અપડેટ કરીએ (હેડર 1 રો છે એટલે +2 કરવું પડે)
                        row_idx = record.index[0] + 2
                        status_col_name = [c for c in df.columns if 'status' in c.lower()]
                        
                        if status_col_name:
                            status_col_idx = df.columns.get_loc(status_col_name[0]) + 1
                            sheet.update_cell(row_idx, status_col_idx, status)
                            st.success("ડેટા સફળતાપૂર્વક અપડેટ થઈ ગયો!")
                            st.rerun()
                        else:
                            st.error("Google Sheet માં 'Status' નામની કોલમ મળી નથી!")
                else:
                    st.error("આ કોડવાળી શાળા મળી નથી!")
            else:
                st.error("Google Sheet માં School Code વાળી કોલમ મળી નથી!")
                
    except Exception as e:
        st.error(f"કનેક્શન કે ડેટામાં ભૂલ છે: {e}")

with tab1: 
    handle_sheet("CAL")
with tab2: 
    handle_sheet("Gyankunj")
