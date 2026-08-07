import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- પેજ સેટઅપ અને કેશિંગ ---
st.set_page_config(page_title="SURAT eWaste Survey", layout="wide")

@st.cache_data(ttl=10) # ડેટા દર 10 સેકન્ડે રિફ્રેશ થાય
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
    # શીટ્સના નામ સેટ કર્યા
    master_sheet_name = f"Data{tab_name}"  # દા.ત. DataCAL અથવા DataGyankunj (મૂળ ડેટા માટે)
    entry_sheet_name = tab_name            # દા.ત. CAL અથવા Gyankunj (એન્ટ્રી સેવ કરવા માટે)
    
    try:
        # બંને શીટ્સમાંથી ડેટા મંગાવો
        m_rows, service, spreadsheet_id = get_sheet_data(master_sheet_name)
        e_rows, _, _ = get_sheet_data(entry_sheet_name)
        
        if len(m_rows) < 2 or len(e_rows) < 2:
            st.warning(f"Google Sheet ({master_sheet_name} અથવા {entry_sheet_name}) માં પૂરતો ડેટા નથી!")
            return
            
        header = [str(c).strip() for c in m_rows[0] if str(c).strip() != ""]
        num_cols = len(header)
        
        # ડેટા ફ્રેમ બનાવવાનું ફંક્શન
        def make_df(rows):
            data = []
            for r in rows[1:]:
                while len(r) < num_cols: r.append("")
                data.append(r[:num_cols])
            return pd.DataFrame(data, columns=header)
            
        m_df = make_df(m_rows) # Master DataFrame
        e_df = make_df(e_rows) # Entry DataFrame
        
        status_col = header[-2]
        
        # --- ૧. ડેશબોર્ડ (Dashboard) ---
        code_cols = [c for c in header if 'code' in c.lower() or 'sch' in c.lower()]
        name_cols = [c for c in header if 'name' in c.lower()]
        c_col = code_cols[0] if code_cols else header[0]
        n_col = name_cols[0] if name_cols else header[1]

        total = len(m_df)
        # Entry શીટમાં કઈ શાળાઓ Completed છે તેનું લિસ્ટ કાઢો
        completed_codes = e_df[e_df[status_col].astype(str).str.strip() == "Completed"][c_col].astype(str).str.strip().tolist()
        completed = len(completed_codes)
        pending = total - completed
        
        # ડાર્ક/લાઈટ થીમ અને મોબાઈલ માટે પરફેક્ટ ડેશબોર્ડ (st.metric નો ઉપયોગ)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label=f"કુલ શાળાઓ ({master_sheet_name})", value=total)
        with col2:
            st.metric(label=f"એન્ટ્રી પૂર્ણ ({entry_sheet_name})", value=completed)
        with col3:
            st.metric(label="બાકી એન્ટ્રી", value=pending)
        
        st.markdown("---") # ડેશબોર્ડ નીચે એક લાઈન દોરવા માટે
        
        # --- ૨. પેન્ડિંગ શાળાઓની યાદી (Pending List) ---
        with st.expander(f"📋 બાકી રહેલી શાળાઓની યાદી જુઓ ({tab_name})"):
            # Master શીટમાંથી એવી શાળાઓ શોધો જે Completed લિસ્ટમાં નથી
            pending_df = m_df[~m_df[c_col].astype(str).str.strip().isin(completed_codes)]
            if not pending_df.empty:
                st.dataframe(pending_df[[c_col, n_col]], use_container_width=True)
            else:
                st.success("બધી જ શાળાઓની એન્ટ્રી પૂર્ણ થઈ ગઈ છે!")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- ૩. શાળા સર્ચ અને ડેટા એન્ટ્રી ---
        school_code = st.text_input(f"🔍 School Code નાખો ({tab_name}):", key=f"input_{tab_name}")
        
        if school_code:
            school_code_str = str(school_code).strip()
            # Master અને Entry બંને શીટમાં આ શાળા શોધો
            m_match = m_df[m_df[c_col].astype(str).str.strip() == school_code_str]
            e_match = e_df[e_df[c_col].astype(str).str.strip() == school_code_str]
            
            if not m_match.empty and not e_match.empty:
                m_row_data = m_match.iloc[0] # ઓરિજિનલ ડેટા (મેક્સ લિમિટ માટે)
                e_row_data = e_match.iloc[0] # એન્ટ્રી ડેટા (અગાઉ ભરેલો ડેટા)
                e_idx = e_match.index[0]     # Entry શીટમાં કઈ લાઈનમાં સેવ કરવું તે
                
                # લાઇવ સ્ટેટસ ઇન્ડિકેટર (Entry શીટમાંથી)
                current_status = str(e_row_data[status_col]).strip()
                if current_status == "Completed":
                    st.markdown("### સ્ટેટસ: <span style='color:green'>✅ એન્ટ્રી પૂર્ણ (Completed)</span>", unsafe_allow_html=True)
                else:
                    st.markdown("### સ્ટેટસ: <span style='color:red'>⏳ બાકી (Pending)</span>", unsafe_allow_html=True)
                
                st.success(f"શાળાની માહિતી મળી ગઈ છે. (મૂળ ડેટા '{master_sheet_name}' મુજબ ચકાસવામાં આવશે)")
                
                updated_inputs = {}
                has_error = False
                
                for i, col in enumerate(header):
                    m_val = str(m_row_data[col]).strip()
                    e_val = str(e_row_data[col]).strip()
                    
                    is_disabled = (i <= 5) or (i >= num_cols - 2)
                    
                    if is_disabled:
                        # ડિસેબલ કોલમમાં Master શીટનો ડેટા બતાવો (જેમ કે નામ, કોડ વગેરે)
                        display_val = m_val 
                        st.text_input(col, value=display_val, disabled=True, key=f"{tab_name}_{col}_{e_idx}")
                        updated_inputs[col] = display_val
                    else:
                        # એડિટ કરવાવાળી કોલમમાં: જો યુઝરે Entry કરી હોય તો e_val, નહીંતર ખાલી (blank)
                        display_val = e_val 
                        user_val = st.text_input(col, value=display_val, key=f"{tab_name}_{col}_{e_idx}")
                        
                        # --- ૪. Max Number Logic (મૂળ Data શીટ સાથે સરખામણી) ---
                        if user_val.isdigit() and m_val.isdigit():
                            if int(user_val) > int(m_val):
                                st.error(f"⚠️ ભૂલ: '{col}' માં તમે મૂળ સંખ્યા ({m_val}) થી મોટી સંખ્યા ({user_val}) ન લખી શકો!")
                                has_error = True 
                        
                        updated_inputs[col] = user_val
                
                # --- ૫. ફેરફાર સેવ કરો (માત્ર Entry શીટમાં જ લખાશે) ---
                if st.button("ફેરફાર સેવ કરો", disabled=has_error, type="primary", key=f"save_{tab_name}_{e_idx}"):
                    with st.spinner(f"માહિતી '{entry_sheet_name}' શીટમાં સેવ થઈ રહી છે..."):
                        sheet_row_idx = e_idx + 2 
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        final_values = []
                        for i, col_name in enumerate(header):
                            if i == num_cols - 2:  
                                final_values.append("Completed")
                            elif i == num_cols - 1: 
                                final_values.append(current_time)
                            else:
                                final_values.append(str(updated_inputs.get(col_name, "")))
                        
                        # માત્ર ને માત્ર Entry શીટમાં અપડેટ થશે, Data શીટ સુરક્ષિત રહેશે!
                        service.spreadsheets().values().update(
                            spreadsheetId=spreadsheet_id, range=f"{entry_sheet_name}!A{sheet_row_idx}",
                            valueInputOption="RAW", body={'values': [final_values[:num_cols]]}
                        ).execute()
                        
                        st.cache_data.clear()
                        st.success("માહિતી સફળતાપૂર્વક સેવ થઈ ગઈ છે!")
                        st.rerun()
            else:
                st.error("આ કોડવાળી શાળા ડેટાબેઝમાં મળી નથી! (શાળાનો કોડ બંને શીટમાં હોવો જરૂરી છે)")

    # અહીં try બ્લોકને પૂરો કરવા માટે except મૂકવામાં આવ્યું છે
    except Exception as e:
        st.error(f"સિસ્ટમ કે કનેક્શનમાં ભૂલ છે: {e}")

with tab1: handle_sheet("CAL")
with tab2: handle_sheet("Gyankunj")
