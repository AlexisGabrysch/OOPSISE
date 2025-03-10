import streamlit as st
from pages.ressources.components import Navbar

st.set_page_config(page_title="Admin", page_icon="📚", layout="wide")
def main():
    Navbar()
    st.title("Hello World!")
    st.write("This is a Streamlit app!")

if __name__ == "__main__":
    main()