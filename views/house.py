"""House: cleaning rota that passes chores on automatically, and a shared shopping list."""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
from datetime import date, timedelta

import streamlit as st

import db
import logic

st.title("🧹 House")
names = db.names()
member_ids = list(names)
today = date.today()

left, right = st.columns(2, gap="large")

# ---------- cleaning rota ----------
with left:
    st.subheader("Cleaning rota")
    st.caption("Ticking off a chore moves it to the next date and passes it to the next flatmate.")
    for c in db.table("SELECT * FROM chores ORDER BY due").itertuples():
        days = (date.fromisoformat(c.due) - today).days
        when = "today" if days == 0 else f"in {days} days" if days > 0 else f"⚠️ {-days} days overdue"
        a, b, d = st.columns([4, 1, 0.5])
        a.write(f"**{c.title}** · {names.get(c.assignee, '?')} · {when}")
        if b.button("Done", key=f"done-{c.id}"):
            start = max(date.fromisoformat(c.due), today)  # overdue: count the interval from today
            db.run("UPDATE chores SET due = ?, assignee = ? WHERE id = ?",
                   ((start + timedelta(days=int(c.every_days))).isoformat(),
                    logic.next_assignee(member_ids, c.assignee), c.id))
            st.rerun()
        if d.button("✕", key=f"del-chore-{c.id}", help="Delete"):
            db.run("DELETE FROM chores WHERE id = ?", (c.id,))
            st.rerun()

    with st.expander("➕ New chore"):
        with st.form("new-chore", clear_on_submit=True):
            title = st.text_input("What?", placeholder="Clean the bathroom")
            every = st.number_input("Every … days", min_value=1, value=7)
            due = st.date_input("First time", value=today, format="DD.MM.YYYY")
            first = st.selectbox("Starts with", member_ids, format_func=names.get)
            if st.form_submit_button("Save", type="primary") and title.strip():
                db.run("INSERT INTO chores (title, every_days, due, assignee) VALUES (?, ?, ?, ?)",
                       (title.strip(), int(every), due.isoformat(), first))
                st.rerun()

# ---------- shopping list ----------
with right:
    st.subheader("Shopping list")
    with st.form("new-item", clear_on_submit=True):
        a, b = st.columns([4, 1])
        item = a.text_input("Item", placeholder="e.g. 2 l oat milk", label_visibility="collapsed")
        if b.form_submit_button("Add") and item.strip():
            db.run("INSERT INTO shopping (item) VALUES (?)", (item.strip(),))
            st.rerun()

    items = db.table("SELECT * FROM shopping ORDER BY done, item")
    if items.empty:
        st.caption("The list is empty.")
    for s in items.itertuples():
        ticked = st.checkbox(s.item, value=bool(s.done), key=f"shop-{s.id}")
        if ticked != bool(s.done):  # the box was just clicked: save the new state
            db.run("UPDATE shopping SET done = ? WHERE id = ?", (int(ticked), s.id))
            st.rerun()
    if items["done"].sum():
        if st.button("Remove ticked items"):
            db.run("DELETE FROM shopping WHERE done = 1")
            st.rerun()
