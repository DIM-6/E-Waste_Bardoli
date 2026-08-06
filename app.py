streamlit.errors.StreamlitAPIException: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:
File "/mount/src/e-waste_bardoli/app.py", line 177, in <module>
    st.download_button(
    ~~~~~~~~~~~~~~~~~~^
        label="📥 અપડેટ કરેલી એક્સેલ ફાઇલ ડાઉનલોડ કરો",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
        ),
        ^^
    )
    ^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 596, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 783, in download_button
    return self._download_button(
           ~~~~~~~~~~~~~~~~~~~~~^
        label=label,
        ^^^^^^^^^^^^
    ...<14 lines>...
        shortcut=shortcut,
        ^^^^^^^^^^^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 1370, in _download_button
    raise StreamlitAPIException(
        f"`st.download_button()` can't be used in an `st.form()`.{FORM_DOCS_INFO}"
    )
