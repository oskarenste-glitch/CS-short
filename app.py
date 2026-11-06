"""WG Organizer: start page. Run with:  streamlit run app.py

Sets up the flat on first start, shows "Who's home today?" in the sidebar and switches between the pages in views/.
"""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import streamlit as st

import db

st.set_page_config(page_title="WG Organizer", page_icon="🏠", layout="wide")

members = db.members()

# First start: nobody lives here yet -> ask for the names and stop until that's done
if members.empty:
    st.title("🏠 WG Organizer")
    st.subheader("Who lives in your flat?")
    with st.form("setup"):
        names = st.text_input("Names, separated by commas", placeholder="Oskar, Peer, Mira, Layla")
        if st.form_submit_button("Create flat", type="primary"):
            for name in [n.strip() for n in names.split(",") if n.strip()]:
                db.run("INSERT INTO members (name) VALUES (?)", (name,))
            st.rerun()
    st.stop()

# Sidebar on every page: who is home today. Cooking suggestions only consider these people.
with st.sidebar:
    all_ids = list(members["id"])
    # keep the earlier choice, drop people who moved out, and count new flatmates as home
    new = [m for m in all_ids if m not in st.session_state.get("known", [])]
    st.session_state["home"] = [m for m in st.session_state.get("home", []) if m in all_ids] + new
    st.session_state["known"] = all_ids
    st.multiselect("Who's home today?", all_ids, key="home", format_func=dict(zip(members["id"], members["name"])).get)

page = st.navigation([
    st.Page("views/split.py", title="Fair Split", icon="💸"),
    st.Page("views/house.py", title="House", icon="🧹"),
    st.Page("views/cooking.py", title="Cooking", icon="🍝"),
    st.Page("views/flatmates.py", title="Flatmates", icon="👥"),
])
page.run()
