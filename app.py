import base64
import json
from pathlib import Path

import streamlit as st

# Import our converter module
from xsd_converter import xsd_to_json_schema


def get_download_link(json_data, filename="schema.json"):
    """Generate a download link for the JSON Schema"""
    json_str = json.dumps(json_data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'data:application/json;base64,{b64}'
    return href


def main():
    st.set_page_config(
        page_title="XSD to JSON Schema Converter",
        page_icon="🔄",
        layout="wide"
    )

    st.title("🔄 XSD to JSON Schema Converter")
    st.write("Upload an XSD file to convert it to JSON Schema")

    uploaded_file = st.file_uploader("Browse your XSD file", type=["xsd"])

    if uploaded_file is not None:
        # Display file details
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
        with col2:
            st.write(f"**Size:** {uploaded_file.size} bytes")

        # Process button
        if st.button("Convert to JSON Schema"):
            # Process the XSD file
            xsd_content = uploaded_file.getvalue()
            with st.spinner("Converting XSD to JSON Schema..."):
                try:
                    json_schema = xsd_to_json_schema(xsd_content)
                    st.success("✅ Conversion successful!")

                    # Show a sample of the generated schema
                    with st.expander("Generated JSON Schema (Preview)", expanded=True):
                        st.json(json_schema)

                    # Provide download button
                    output_filename = f"{Path(uploaded_file.name).stem}_schema.json"
                    download_link = get_download_link(json_schema, filename=output_filename)

                    st.markdown(
                        f'<a href="{download_link}" download="{output_filename}" target="_blank">'
                        f'<button style="background-color:#4CAF50;color:white;padding:10px 24px;'
                        f'border-radius:8px;font-size:16px;cursor:pointer;border:none;margin:10px 0;">'
                        f'Download JSON Schema</button>'
                        f'</a>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
