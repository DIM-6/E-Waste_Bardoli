import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets કનેક્શન સેટઅપ
def get_sheet(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Secrets માંથી ડેટા લોડ કરીને પ્રાઈવેટ કી ની લાઈન સેટ કરે છે
    creds_dict = dict(st.secrets["gcp"])
    if '\\n' in creds_dict['private_key']:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # તમારી Google Sheet ની લિંક
    return client.open_by_url('https://docs.google.com/spreadsheets/d/1oAeqzK2zgifwn--u2jjYicfmlhpvqhwNAXi1ErMfrIQ/edit').worksheet(sheet_name)

st.title("🏫 SURAT eWaste Survey")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        sheet = get_sheet(tab_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            # ડેટા શોધવા માટે
            record = df[df['Sch. Code'].astype(str) == str(school_code)]
            
            if not record.empty:
                st.write(f"શાળાનું નામ: {record.iloc[0]['School Name']}")
                status = st.selectbox("Status", ["Pending", "Completed"], key=f"sel_{tab_name}")
                
                if st.button("સેવ કરો", key=f"btn_{tab_name}"):
                    row_idx = record.index[0] + 2
                    # Google Sheet માં Status કોલમ અપડેટ કરે છે
                    sheet.update_cell(row_idx, df.columns.get_loc('Status') + 1, status)
                    st.success("ડેટા સફળતાપૂર્વક અપડેટ થઈ ગયો!")
                    st.rerun()
            else:
                st.error("આ કોડવાળી શાળા મળી નથી!")
    except Exception as e:
        st.error(f"કનેક્શનમાં ભૂલ છે: {e}")

with tab1: 
    handle_sheet("CAL")
with tab2: 
    handle_sheet("Gyankunj")
    
