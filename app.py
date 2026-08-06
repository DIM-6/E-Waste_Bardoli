import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SURAT eWaste Survey 2026-27", layout="wide")

st.title("🏫 SURAT eWaste Survey - School Data Update Form")

db_file = "ewaste.db"


@st.cache_data
def load_data_from_db():
  if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql("SELECT * FROM school_data", conn)
    conn.close()
    return df
  return None


# જો ડેટાબેઝ ફાઇલ ન હોય તો ફાઇલ અપલોડ કરવાનો ઓપ્શન આપવો
if not os.path.exists(db_file):
  uploaded_file = st.file_uploader(
      "કૃપા કરીને તમારી 'E-Waste_Sch.ods' અથવા SQLite ફાઇલ અહીં અપલોડ કરો",
      type=["ods", "xlsx", "db"],
  )
  if uploaded_file is not None:
    if uploaded_file.name.endswith(".db"):
      with open(db_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
      st.success("ડેટાબેઝ સફળતાપૂર્વક અપલોડ થઈ ગયો છે! પેજ રિફ્રેશ કરો.")
      st.rerun()
    else:
      try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
        conn = sqlite3.connect(db_file)
        df.to_sql("school_data", conn, if_exists="replace", index=False)
        conn.close()
        st.success("ഫાઇલ સફળતાપૂર્વક ડેટાબેઝમાં કન્વર્ટ થઈ ગઈ છે!")
        st.rerun()
      except Exception as e:
        st.error(f"ભૂલ આવી: {e}")

df = load_data_from_db()

if df is not None:
  df.columns = [str(c).strip() for c in df.columns]

  for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .replace("nan", "")
    )

  code_col = None
  for col in df.columns:
    if "code" in col.lower() or "sch" in col.lower():
      code_col = col
      break
  if not code_col:
    code_col = df.columns[4]

  st.sidebar.header("🔍 શાળા શોધો")
  school_code_input = st.sidebar.text_input("School Code નાખો:")

  if school_code_input:
    matched_indices = df[df[code_col] == school_code_input.strip()].index

    if not matched_indices.empty:
      st.success("શાળાની માહિતી સફળતાપૂર્વક મળી ગઈ છે!")
      idx = matched_indices[0]
      row = df.loc[idx]

      with st.form("ewaste_form"):
        school_name_col = next(
            (c for c in df.columns if "school name" in c.lower()), df.columns[5]
        )
        st.subheader(f"શાળાનું નામ: {row.get(school_name_col, 'N/A')}")

        cols = st.columns(3)
        updated_values = {}
        original_max_values = {}

        target_columns = [
            "Standalone desktop computers",
            "Shared computing host desktops",
            "Computer with dual display 18.5\"LED Backlit",
            '40" or higher LCD display with VGA splitter, external voltage stabilizer',
            "Nodes of Shared Computing with Monitor, keyboard, Mouse",
            "PC Sharing Kit",
            "Speakers",
            "Dot Matrix Printers",
            "16 Port Network Switch",
        ]

        non_editable_cols = [
            "Sr.",
            "District",
            "Block",
            "Village",
            "Sch. Code",
            "School Name",
        ]

        for i, col_name in enumerate(df.columns):
          col_target = cols[i % 3]
          val = str(row[col_name]) if row[col_name] != "nan" else ""

          with col_target:
            if any(
                ne.lower() in col_name.lower() for ne in non_editable_cols
            ):
              st.text_input(
                  str(col_name), value=val, disabled=True, key=f"input_{i}"
              )
              updated_values[col_name] = val
            elif "૨૦૧૧" in col_name or "2011" in col_name or "લેબ" in col_name:
              options = ["", "હા-૧", "ના-ર"]
              default_idx = options.index(val) if val in options else 0
              updated_values[col_name] = st.selectbox(
                  str(col_name), options=options, index=default_idx, key=f"input_{i}"
              )
            elif any(
                target.lower() in col_name.lower() for target in target_columns
            ):
              max_val = int(val) if val.isdigit() else 9999
              original_max_values[col_name] = max_val
              current_val = int(val) if val.isdigit() else 0

              updated_values[col_name] = st.number_input(
                  f"{col_name} (Max: {max_val})",
                  min_value=0,
                  max_value=max_val,
                  value=current_val,
                  step=1,
                  key=f"input_{i}",
              )
            else:
              updated_values[col_name] = st.text_input(
                  str(col_name), value=val, key=f"input_{i}"
              )

        submit = st.form_submit_button("💾 માહિતી સેવ કરો")
        if submit:
          error_occurred = False
          for col_name, max_limit in original_max_values.items():
            if int(updated_values[col_name]) > max_limit:
              st.error(
                  f"ભૂલ: '{col_name}' માં મહત્તમ {max_limit} જ ભરી શકાય છે!"
              )
              error_occurred = True

          if not error_occurred:
            for col_name, new_val in updated_values.items():
              if not any(
                  ne.lower() in col_name.lower() for ne in non_editable_cols
              ):
                df.loc[idx, col_name] = str(new_val)

            # SQLite ડેટાબેઝમાં ડેટા અપડેટ કરવો
            conn = sqlite3.connect(db_file)
            df.to_sql("school_data", conn, if_exists="replace", index=False)
            conn.close()

            st.success(
                "માહિતી સફળતાપૂર્વક ડેટાબેઝમાં અપડેટ અને સેવ થઈ ગઈ છે!"
            )

            # એક્સેલ ફાઇલ ડાઉનલોડ કરવા માટે
            output_file = "SURAT_eWaste_Updated.xlsx"
            df.to_excel(output_file, index=False)
            with open(output_file, "rb") as f:
              st.download_button(
                  label="📥 અપડેટ કરેલી એક્સેલ ફાઇલ ડાઉનલોડ કરો",
                  data=f,
                  file_name="SURAT_eWaste_Updated.xlsx",
                  mime=(
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  ),
              )
    else:
      st.warning("આવા School Code વાળી કોઈ શાળા મળતી નથી.")
  else:
    st.info("👈 કૃપા કરીને ડાબી બાજુના બોક્સમાં School Code દાખલ કરો.")
else:
  st.warning("કૃપા કરીને ફાઇલ અપલોડ કરો.")
