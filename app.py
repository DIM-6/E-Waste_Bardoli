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
                    
                    # 'Standalone desktop computers' અને '600 VA Line Interactive UPS' ના ઇન્ડેક્સ શોધી લઈએ
                    cols_list = list(df.columns)
                    try:
                        start_limit_idx = cols_list.index("Standalone desktop computers")
                        # 600 VA વાળી કોલમનું નામ બરાબર મેચ થાય તે માટે શોધીએ
                        end_limit_idx = [i for i, c in enumerate(cols_list) if "600 VA" in c][0]
                    except:
                        start_limit_idx = 12  # ડિફોલ્ટ અંદાજિત રેન્જ
                        end_limit_idx = 25

                    with st.form(key=f"form_{tab_name}"):
                        updated_data = {}
                        has_error = False
                        
                        for idx, col in enumerate(cols_list):
                            val = str(school_row[col]) if pd.notna(school_row[col]) else ""
                            is_locked = idx <= 5  # Sr. થી School Name સુધી લોક
                            
                            if idx == 6:  # કોમ્પ્યુટર લેબ ડ્રોપ-ડાઉન
                                options = ["હા-૧", "ના-૨"]
                                default_idx = options.index(val) if val in options else 0
                                updated_data[col] = st.selectbox(col, options, index=default_idx)
                                
                            elif start_limit_idx <= idx <= end_limit_idx:
                                # આ રેન્જમાં માત્ર હોલ નંબર અને ઓરિજિનલ ડેટાથી વધારે ન હોવું જોઈએ
                                user_input = st.text_input(col, value=val)
                                
                                # વેલિડેશન ચેક
                                original_val_str = val.strip()
                                original_num = int(original_val_str) if original_val_str.isdigit() else 0
                                
                                if user_input.strip().isdigit():
                                    user_num = int(user_input.strip())
                                    if user_num > original_num:
                                        st.error(f"❌ '{col}' માં મૂળ આંકડા ({original_num}) કરતા વધારે વેલ્યુ નાખી શકાતી નથી!")
                                        has_error = True
                                    else:
                                        updated_data[col] = str(user_num)
                                else:
                                    if user_input.strip() != "":
                                        st.error(f"❌ '{col}' માં ફક્ત પૂર્ણાંક સંખ્યા (Whole Number) જ માન્ય છે!")
                                        has_error = True
                                    updated_data[col] = user_input
                            else:
                                updated_data[col] = st.text_input(col, value=val, disabled=is_locked)
                        
                        submit_button = st.form_submit_button(label="ફેરફાર સેવ કરો")
                        
                        if submit_button:
                            if has_error:
                                st.error("કૃપા કરીને ભૂલો સુધારીને ફરીથી પ્રયત્ન કરો.")
                            else:
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
