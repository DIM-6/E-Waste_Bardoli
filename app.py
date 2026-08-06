import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SURAT eWaste Survey 2026-27", layout="wide")

st.title("🏫 SURAT eWaste Survey Portal")

# બે અલગ ટેબ બનાવવી
tab1, tab2 = st.tabs(["💻 CAL-LAB", "📚 Gyankunj E-Waste"])


# ---------------------------------------------------------
# ફંક્શન: જે તે ટેબ માટે ડેટા હેન્ડલ કરવા માટે
# ---------------------------------------------------------
def handle_survey_portal(tab_name, db_file, default_file_msg):
  st.header(f"📊 {tab_name} Survey Portal")

  def load_data_from_db(db):
    if os.path.exists(db):
      conn = sqlite3.connect(db)
      dframe = pd.read_sql("SELECT * FROM school_data", conn)
      conn.close()
      return dframe
    return None

  # જો ડેટાબેઝ ફાઇલ ન હોય તો જ અપલોડ ઓપ્શન આપવો (માત્ર ૧ જ વાર પૂછશે)
  if not os.path.exists(db_file):
    uploaded_file = st.file_uploader(
        f"કૃપા કરીને '{default_file_msg}' અથવા SQLite ફાઇલ અહીં અપલોડ કરો",
        type=["ods", "xlsx", "db"],
        key=f"uploader_{tab_name}",
    )
    if uploaded_file is not None:
      if uploaded_file.name.endswith(".db"):
        with open(db_file, "wb") as f:
          f.write(uploaded_file.getbuffer())
        st.success("ડેટાબેઝ સફળતાપૂર્વક અપલોડ થઈ ગયો છે! પેજ રિફ્રેશ કરો.")
        st.rerun()
      else:
        try:
          dframe = pd.read_excel(uploaded_file, sheet_name=0, header=0)
          if "Status" not in dframe.columns:
            dframe["Status"] = "Pending"
          conn = sqlite3.connect(db_file)
          dframe.to_sql("school_data", conn, if_exists="replace", index=False)
          conn.close()
          st.success("ફાઇલ સફળતાપૂર્વક ડેટાબેઝમાં કન્વર્ટ થઈ ગઈ છે!")
          st.rerun()
        except Exception as e:
          st.error(f"ભૂલ આવી: {e}")
    return

  df = load_data_from_db(db_file)

  if df is not None:
    df.columns = [str(c).strip() for c in df.columns]

    if "Status" not in df.columns:
      df["Status"] = "Pending"

    for col in df.columns:
      if col != "Status":
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

    st.sidebar.header(f"🔍 {tab_name} - સર્વે સ્ટેટસ")

    total_schools = len(df)
    completed_schools = (
        len(df[df["Status"] == "Completed"])
        if "Status" in df.columns
        else 0
    )
    pending_schools = total_schools - completed_schools

    st.sidebar.markdown(f"**કુલ શાળાઓ:** {total_schools}")
    st.sidebar.markdown(f"🟢 **પૂર્ણ થયેલ (Completed):** {completed_schools}")
    st.sidebar.markdown(f"🟡 **બાકી (Pending):** {pending_schools}")
    st.sidebar.markdown("---")

    school_code_input = st.sidebar.text_input(
        f"School Code નાખો ({tab_name}):", key=f"input_code_{tab_name}"
    )

    if school_code_input:
      matched_indices = df[df[code_col] == school_code_input.strip()].index

      if not matched_indices.empty:
        st.success("શાળાની માહિતી સફળતાપૂર્વક મળી ગઈ છે!")
        idx = matched_indices[0]
        row = df.loc[idx]
        current_school_code = str(row[code_col])

        session_key_limits = f"original_limits_{tab_name}"
        if session_key_limits not in st.session_state:
          st.session_state[session_key_limits] = {}

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

        if current_school_code not in st.session_state[session_key_limits]:
          st.session_state[session_key_limits][current_school_code] = {}
          for col_name in df.columns:
            if any(t.lower() in col_name.lower() for t in target_columns):
              val = str(row[col_name]).strip()
              st.session_state[session_key_limits][current_school_code][
                  col_name
              ] = (int(val) if val.isdigit() else 0)

        current_status = str(row.get("Status", "Pending"))
        if current_status.strip() == "Completed":
          st.success(
              "✅ આ શાળાની માહિતી અગાઉ પૂર્ણ થઈ ગઈ છે (Completed). તમે ફરીથી"
              " સુધારો કરી શકો છો."
          )
        else:
          st.warning(
              "⚠️ આ શાળાની માહિતી હજુ ભરવાની બાકી છે (Pending)."
          )

        with st.form(f"form_{tab_name}"):
          school_name_col = next(
              (c for c in df.columns if "school name" in c.lower()),
              df.columns[5],
          )
          st.subheader(f"શાળાનું નામ: {row.get(school_name_col, 'N/A')}")

          cols = st.columns(3)
          updated_values = {}

          non_editable_cols = [
              "Sr.",
              "District",
              "Block",
              "Village",
              "Sch. Code",
              "School Name",
              "Status",
          ]

          for i, col_name in enumerate(df.columns):
            if col_name == "Status":
              continue
            col_target = cols[i % 3]
            val = str(row[col_name]) if row[col_name] != "nan" else ""

            with col_target:
              if any(ne.lower() in col_name.lower() for ne in non_editable_cols):
                st.text_input(
                    str(col_name),
                    value=val,
                    disabled=True,
                    key=f"{tab_name}_input_{i}",
                )
                updated_values[col_name] = val
              elif "૨૦૧૧" in col_name or "2011" in col_name or "લેબ" in col_name:
                options = ["", "હા-૧", "ના-ર"]
                default_idx = options.index(val) if val in options else 0
                updated_values[col_name] = st.selectbox(
                    f"{col_name} (રજિસ્ટર)",
                    options=options,
                    index=default_idx,
                    key=f"{tab_name}_input_{i}",
                )
              elif any(
                  target.lower() in col_name.lower() for target in target_columns
              ):
                max_val = st.session_state[session_key_limits][
                    current_school_code
                ].get(col_name, 0)
                current_val = int(val) if val.isdigit() else 0

                updated_values[col_name] = st.number_input(
                    f"{col_name} (Max allowed: {max_val})",
                    min_value=0,
                    max_value=99999,
                    value=current_val,
                    step=1,
                    key=f"{tab_name}_input_{i}",
                )
              else:
                updated_values[col_name] = st.text_input(
                    f"{col_name} (ફરજિયાત)",
                    value=val,
                    key=f"{tab_name}_input_{i}",
                )

          submit = st.form_submit_button("💾 માહિતી સેવ કરો")
          form_submitted = submit

        if form_submitted:
          error_occurred = False

          # ૧. ખાલી ખાના ચેક કરવા
          for col_name, new_val in updated_values.items():
            if not any(
                ne.lower() in col_name.lower() for ne in non_editable_cols
            ):
              if (
                  str(new_val).strip() == "" or str(new_val).strip() == "None"
              ):
                st.error(
                    f"❌ ભૂલ: '{col_name}' ખાલી રાખી શકાતું નથી. આ માહિતી ભરવી"
                    " ફરજિયાત છે!"
                )
                error_occurred = True

          # ૨. ઓરિજિનલ લિમિટ સાથે સરખામણી
          if not error_occurred:
            school_limits = st.session_state[session_key_limits][
                current_school_code
            ]
            for col_name, max_limit in school_limits.items():
              entered_val = int(updated_values[col_name])
              if entered_val > max_limit:
                st.error(
                    f"❌ ભૂલ: '{col_name}' માં વધુમાં વધુ (Max) {max_limit} જ વેલ્યુ"
                    f" હોઈ શકે છે. તમે તેનાથી મોટી ({entered_val}) વેલ્યુ ભરી"
                    " છે!"
                )
                error_occurred = True

          # ૩. સેવ કરવું
          if not error_occurred:
            for col_name, new_val in updated_values.items():
              if not any(
                  ne.lower() in col_name.lower() for ne in non_editable_cols
              ):
                df.loc[idx, col_name] = str(new_val)

            df.loc[idx, "Status"] = "Completed"

            conn = sqlite3.connect(db_file)
            df.to_sql("school_data", conn, if_exists="replace", index=False)
            conn.close()

            st.success("Data is updated successfully")
            st.balloons()

      else:
        st.warning("આવા School Code વાળી કોઈ શાળા મળતી નથી.")
    else:
      st.info(f"👈 કૃપા કરીને ડાબી બાજુના બોક્સમાં School Code દાખલ કરો.")


# ---------------------------------------------------------
# ટેબ ૧: CAL-LAB માટે
# ---------------------------------------------------------
with tab1:
  handle_survey_portal(
      "CAL-LAB", "ewaste_callab.db", "E-Waste_Sch.ods (CAL-LAB)"
  )

# ---------------------------------------------------------
# ટેબ ૨: Gyankunj E-Waste માટે
# ---------------------------------------------------------
with tab2:
  handle_survey_portal(
      "Gyankunj", "ewaste_gyankunj.db", "E-Waste_GyanSch.ods (Gyankunj)"
  )
