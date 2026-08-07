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

st.title("🏫 SURAT eWaste Survey - Data Form")
st.warning("⚠️ **સૂચના:** હાલ આ સાઇટ પર કામ ચાલી રહ્યું છે, જેથી હમણાં કોઈ પણ જાતની એન્ટ્રી કરવી નહીં.")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        sheet = get_sheet(tab_name)
        rows = sheet.get_all_values()
        if len(rows) < 2:
            st.warning("Google Sheet માં કોઈ ડેટા નથી!")
            return
            
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.columns = df.columns.str.strip()

        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            code_col = [c for c in df.columns if 'code' in c.lower() or 'sch' in c.lower()]
            
            if code_col:
                actual_code_col = code_col[0]
                match_indices = df[df[actual_code_col].astype(str).str.strip() == str(school_code).strip()].index
                
                if not match_indices.empty:
                    row_idx = match_indices[0]
                    school_row = df.iloc[row_idx]
                    
                    st.success("શાળાની માહિતી મળી ગઈ છે. નીચે ફોર્મમાં વિગતો ભરો:")
                    
                    with st.form(key=f"form_{tab_name}"):
                        updated_data = {}
                        
                        #enumerate વાપરીએ જેથી આપણને કોલમનો નંબર (index) મળે
                        for idx, col in enumerate(df.columns):
                            val = str(school_row[col]) if pd.notna(school_row[col]) else ""
                            
                            # જો 6 નંબરની કોલમ હોય (તમારા ફોટા મુજબ), તો જ ડ્રોપ-ડાઉન આપો
                            if idx == 6:
                                options = ["હા-૧", "ના-૨"]
                                default_idx = options.index(val) if val in options else 0
                                updated_data[col] = st.selectbox(col, options, index=default_idx)
                            else:
                                updated_data[col] = st.text_input(col, value=val)
                        
                        submit_button = st.form_submit_button(label="ફેરફાર સેવ કરો")
                        
                        if submit_button:
                            sheet_row_idx = row_idx + 2 
                            new_values = [updated_data[col] for col in df.columns]
                            
                            sheet.update(f"A{sheet_row_idx}", [new_values])
                            st.success("માહિતી સફળતાપૂર્વક Google Sheet માં સેવ થઈ ગઈ છે!")
                            st.rerun()
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
