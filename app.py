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

st.title("🏫 SURAT eWaste Survey - Data Entry")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

def handle_sheet(tab_name):
    try:
        sheet = get_sheet(tab_name)
        rows = sheet.get_all_values()
        if len(rows) < 2:
            st.warning("Google Sheet માં કોઈ ડેટા નથી!")
            return
            
        # પહેલી રો ને હેડર બનાવીએ
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.columns = df.columns.str.strip()

        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            code_col = [c for c in df.columns if 'code' in c.lower() or 'sch' in c.lower()]
            
            if code_col:
                actual_code_col = code_col[0]
                # તે કોડવાળી રો શોધીએ
                match_indices = df[df[actual_code_col].astype(str).str.strip() == str(school_code).strip()].index
                
                if not match_indices.empty:
                    row_idx = match_indices[0]
                    
                    # તે પર્ટીક્યુલર શાળાનો ડેટા કાઢીએ
                    school_data = df.iloc[[row_idx]]
                    
                    st.success("શાળાની માહિતી મળી ગઈ છે. તમે નીચે ફેરફાર કરી શકો છો:")
                    
                    # st.data_editor થી યુઝર ટેબલની અંદર જ ડેટા એડિટ કરી શકશે
                    edited_df = st.data_editor(school_data, key=f"editor_{tab_name}", num_rows="fixed")
                    
                    if st.button("ફેરફાર સેવ કરો", key=f"btn_{tab_name}"):
                        # એડિટ થયેલી માહિતીને ગૂગલ શીટમાં પાછી અપડેટ કરીએ
                        sheet_row_idx = row_idx + 2  # હેડર અને 0-indexing ને કારણે +2
                        updated_values = edited_df.iloc[0].tolist()
                        
                        # આખી રો એકસાથે ગૂગલ શીટમાં અપડેટ થઈ જશે
                        sheet.update(f"A{sheet_row_idx}", [updated_values])
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
