import streamlit as st

def nav_page(page_name):
    """
    Navigate to a different page in the Streamlit app.

    Args:
        page_name (str): The name of the page to navigate to. This should match the expected query parameter value.

    Raises:
        ValueError: If the page_name is invalid (e.g., empty or not a string).
    """
    if not page_name or not isinstance(page_name, str):
        raise ValueError("Invalid page name. It must be a non-empty string.")
    
    # Set the query parameter to navigate to the desired page
    st.experimental_set_query_params(page=page_name)