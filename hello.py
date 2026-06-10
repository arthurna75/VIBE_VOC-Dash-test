import streamlit as st

st.set_page_config(page_title="Hello", layout="centered")

st.title("Hello Streamlit! 👋")

st.write("Welcome to your first Streamlit app!")

name = st.text_input("What's your name?", "World")
st.write(f"Hello, {name}!")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Metric 1", "100", "+5")
with col2:
    st.metric("Metric 2", "200", "-10")
with col3:
    st.metric("Metric 3", "300", "+20")

if st.button("Click me!"):
    st.balloons()
