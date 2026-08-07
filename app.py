import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Google Sheets API કનેક્શન (લેટેસ્ટ અને એરર ફ્રી પદ્ધતિ)
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
st.warning("⚠️ **સૂચના:** હાલ આ સાઇટ પર કામ ચાલી રહ્યું છે, જેથી હમણાં કોઈ પણ જાતની એન્ટ્રી કરવી નહીં.")

tab1, tab2 = st.tabs(["💻 CAL", "📚 Gyankunj"])

if 'original_df_cache' not in st.session_state:
    st.session_state['original_df_cache'] = {}

def handle_sheet(tab_name):
    try:
        rows, service, spreadsheet_id, range_name = get_sheet_data(tab_name)
        if len(rows) < 2:
            st.warning("Google Sheet માં કોઈ ડેટા નથી!")
            return
            
        current_df = pd.DataFrame(rows[1:], columns=rows[0])
        current_df.columns = current_df.columns.str.strip()

        if tab_name not in st.session_state['original_df_cache']:
            st.session_state['original_df_cache'][tab_name] = current_df.copy()

        original_df = st.session_state['original_df_cache'][tab_name]

        # --- Entry Status અને TimeStamp કૉલમ સેટઅપ ---
        status_col = "Entry Status"
        ts_col = "TimeStamp"
        
        # ગણતરી: માત્ર 'Completed' લખેલું હોય તેને જ પૂર્ણ ગણવું
        total_schools = len(current_df)
        if status_col in current_df.columns:
            completed_entries = len(current_df[current_df[status_col].astype(str).str.strip() == "Completed"])
        else:
            completed_entries = 0
        pending_entries = total_schools - completed_entries

        # --- ડેશબોર્ડ (મોબાઈલ અને ડેસ્કટોપ માટે ફ્લેક્સબોક્સ) ---
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
                <div style="text-align: center;">
                    <div style="font-size: 12px; color: #555;">કુલ શાળાઓ</div>
                    <div style="font-size: 20px; font-weight: bold;">{total_schools}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 12px; color: #555;">એન્ટ્રી પૂર્ણ</div>
                    <div style="font-size: 20px; font-weight: bold; color: green;">{completed_entries}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 12px; color: #555;">બાકી એન્ટ્રી</div>
                    <div style="font-size: 20px; font-weight: bold; color: red;">{pending_entries}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- પેન્ડિંગ શાળાઓ જોવા માટેનું બટન ---
        with st.expander(f"📋 બાકી રહેલી શાળાઓનું લિસ્ટ જુઓ ({tab_name})"):
            if st.button(f"પેન્ડિંગ શાળાઓ યાદી મેળવો", key=f"btn_pending_{tab_name}"):
                code_col_list = [c for c in current_df.columns if 'code' in c.lower() or 'sch' in c.lower()]
                name_col_list = [c for c in current_df.columns if 'name' in c.lower()]
                if code_col_list and name_col_list:
                    c_col = code_col_list[0]
                    n_col = name_col_list[0]
                    if status_col in current_df.columns:
                        pending_df = current_df[current_df[status_col].astype(str).str.strip() != "Completed"]
                    else:
                        pending_df = current_df
                    st.dataframe(pending_df[[c_col, n_col]])
                else:
                    st.error("કોલમ મળી નથી!")

        school_code = st.text_input(f"School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            code_col = [c for c in current_df.columns if 'code' in c.lower() or 'sch' in c.lower()]
            
            if code_col:
                actual_code_col = code_col[0]
                match_indices = current_df[current_df[actual_code_col].astype(str).str.strip() == str(school_code).strip()].index
                
                if not match_indices.empty:
                    row_idx = match_indices[0]
                    current_school_row = current_df.iloc[row_idx]
                    original_school_row = original_df.iloc[row_idx]
                    
                    st.success("શાળાની માહિતી મળી ગઈ છે. નીચે ફોર્મમાં વિગતો ભરો:")
                    
                    cols_list = list(current_df.columns)
                    try:
                        start_limit_idx = cols_list.index("Standalone desktop computers")
                        end_limit_idx = [i for i, c in enumerate(cols_list) if "600 VA" in c][0]
                    except:
                        start_limit_idx = 12
                        end_limit_idx = 25

                    with st.form(key=f"form_{tab_name}"):
                        updated_data = {}
                        has_error = False
                        
                        for idx, col in enumerate(cols_list):
                            # Entry Status અને TimeStamp કૉલમ ફોર્મમાં એડિટ કરવા માટે નહીં દેખાય
                            if col in [status_col, ts_col]:
                                updated_data[col] = str(current_school_row[col]) if pd.notna(current_school_row[col]) else ""
                                continue
                                
                            val = str(current_school_row[col]) if pd.notna(current_school_row[col]) else ""
                            is_locked = idx <= 5  
                            
                            if idx == 6:  
                                options = ["હા-૧", "ના-૨"]
                                default_idx = options.index(val) if val in options else 0
                                updated_data[col] = st.selectbox(col, options, index=default_idx)
                                
                            elif start_limit_idx <= idx <= end_limit_idx:
                                user_input = st.text_input(col, value=val)
                                
                                orig_val_str = str(original_school_row[col]).strip()
                                original_num = int(orig_val_str) if orig_val_str.isdigit() else 0
                                
                                if user_input.strip() == "":
                                    st.error(f"❌ '{col}' ખાલી રાખી શકાતી નથી!")
                                    has_error = True
                                elif user_input.strip().isdigit():
                                    user_num = int(user_input.strip())
                                    if user_num > original_num:
                                        st.error(f"❌ '{col}' માં મૂળ આંકડા ({original_num}) કરતા વધારે વેલ્યુ નાખી શકાતી નથી!")
                                        has_error = True
                                    else:
                                        updated_data[col] = str(user_num)
                                else:
                                    st.error(f"❌ '{col}' માં ફક્ત પૂર્ણાંક સંખ્યા (Whole Number) જ માન્ય છે!")
                                    has_error = True
                                    updated_data[col] = user_input
                            else:
                                updated_data[col] = st.text_input(col, value=val, disabled=is_locked)
                        
                        # ફોર્મ સબમિટ બટન
                        submit_button = st.form_submit_button(label="ફેરફાર સેવ કરો")
                        
                        if submit_button:
                            if has_error:
                                st.error("કૃપા કરીને બધી ભૂલો સુધારીને ફરીથી પ્રયત્ન કરો.")
                            else:
                                with st.spinner('માહિતી સેવ થઈ રહી છે, કૃપા કરીને રાહ જુઓ...'):
                                    sheet_row_idx = row_idx + 2 
                                    
                                    # Entry Status માં "Completed" અને TimeStamp માં વર્તમાન સમય સેટ કરો
                                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    
                                    if status_col in cols_list:
                                        updated_data[status_col] = "Completed"
                                    if ts_col in cols_list:
                                        updated_data[ts_col] = current_time
                                        
                                    new_values = [updated_data[col] for col in cols_list]
                                    
                                    body = {'values': [new_values]}
                                    service.spreadsheets().values().update(
                                        spreadsheetId=spreadsheet_id,
                                        range=f"{tab_name}!A{sheet_row_idx}",
                                        valueInputOption="RAW",
                                        body=body
                                    ).execute()
                                    
                                    st.cache_data.clear()
                                    st.success(f"માહિતી સફળતાપૂર્વક Google Sheet માં સેવ થઈ ગઈ છે! (Time: {current_time})")
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
