import base64
import requests
import streamlit as st

BACKEND_URL = "http://localhost:5000"  # Flask backend URL


# -------- Helper: Backend calls --------
def register_user(username: str, password: str):
    resp = requests.post(
        f"{BACKEND_URL}/api/register",
        json={"username": username, "password": password},
        timeout=10,
    )
    return resp.json(), resp.status_code


def login_user(username: str, password: str):
    resp = requests.post(
        f"{BACKEND_URL}/api/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    return resp.json(), resp.status_code


def forgot_password(username: str, new_password: str):
    resp = requests.post(
        f"{BACKEND_URL}/api/forgot_password",
        json={"username": username, "new_password": new_password},
        timeout=10,
    )
    return resp.json(), resp.status_code


def send_nl_query(user_id: int, query: str):
    resp = requests.post(
        f"{BACKEND_URL}/api/nl_query",
        json={"user_id": user_id, "query": query},
        timeout=60,
    )
    return resp.json(), resp.status_code


def fetch_notes(user_id: int):
    resp = requests.get(
        f"{BACKEND_URL}/api/notes",
        params={"user_id": user_id},
        timeout=10,
    )
    return resp.json(), resp.status_code


# -------- Streamlit App Config --------
st.set_page_config(page_title="AI Notepad", page_icon="📝", layout="wide")

# ---------- Custom CSS (blue theme + floating animation) ----------
st.markdown(
    """
    <style>
    :root {
        --main-blue: #90e0ef;
        --deep-blue: #0077b6;
        --soft-blue: #caf0f8;
        --bg-gradient-start: #f0fbff;
        --bg-gradient-end: #e0f7ff;
    }

    .stApp {
        background: linear-gradient(135deg, var(--bg-gradient-start), var(--bg-gradient-end));
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Note cards */
    .note-card {
        background-color: #ffffff;
        padding: 0.9rem 1.1rem;
        border-radius: 0.9rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
        border: 1px solid #e0f2ff;
        margin-bottom: 0.6rem;
        width: 100%;
        box-sizing: border-box;
    }

    .note-topic {
        font-weight: 600;
        color: #023047;
        margin-bottom: 0.15rem;
        font-size: 0.98rem;
    }

    .note-meta {
        font-size: 0.78rem;
        color: #6c757d;
        margin-top: 0.15rem;
    }

    .note-message {
        margin-top: 0.25rem;
        margin-bottom: 0.1rem;
        font-size: 0.94rem;
        color: #333;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 999px;
        padding: 0.4rem 1.2rem;
        border: none;
        background: linear-gradient(135deg, var(--deep-blue), var(--main-blue));
        color: white;
        font-weight: 600;
        cursor: pointer;
    }

    .stButton>button:hover {
        filter: brightness(1.05);
        box-shadow: 0 4px 12px rgba(0,119,182,0.35);
    }

    /* Text area */
    textarea {
        border-radius: 0.7rem !important;
        border: 1px solid #cde4ff !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f3fbff;
        border-right: 1px solid #e0f2ff;
    }

    /* AI loading bubble */
    .ai-loading {
        display: inline-block;
        padding: 0.6rem 1rem;
        border-radius: 999px;
        background-color: #ffffff;
        border: 1px solid #cde4ff;
        font-size: 0.9rem;
        color: #1d3557;
        margin-bottom: 0.5rem;
    }

    .your-notes-header {
        margin-bottom: 0.4rem;
        color: #003049;
    }

    /* Floating animation for hero illustration */
    @keyframes floaty {
        0%   { transform: translateY(0px); }
        50%  { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .floating-hero {
        animation: floaty 3s ease-in-out infinite;
        display: flex;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "user" not in st.session_state:
    st.session_state.user = None


# ---------- Helper: render a single note ----------
def render_single_note(note: dict):
    st.markdown(
        f"""
        <div class="note-card">
            <div class="note-topic">🗂 {note.get("topic", "")}</div>
            <div class="note-message">{note.get("message", "")}</div>
            <div class="note-meta">
                ID: {note.get("note_id")} · Last update: {note.get("last_update")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Helper: hero image as base64 ----------
def get_hero_image_html(path: str = "hero_notes.png", width: int = 480) -> str:
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        return f"""
        <div class="floating-hero">
            <img src="data:image/png;base64,{b64}" width="{width}" />
        </div>
        """
    except FileNotFoundError:
        return '<div style="text-align:center; color:#ff4d4f;">hero_notes.png not found</div>'


# ---------- Sidebar: login / register / forgot ----------
with st.sidebar:
    st.header("Account")

    if st.session_state.user is None:
        tab_login, tab_register, tab_forgot = st.tabs(
            ["Login", "Register", "Forgot Password"]
        )

        # ----- Register tab -----
        with tab_register:
            reg_username = st.text_input("Choose a username")
            reg_password = st.text_input(
                "Choose a password", type="password", key="reg_pw"
            )
            if st.button("Register"):
                if not reg_username or not reg_password:
                    st.error("Username and password required.")
                else:
                    with st.spinner("Creating your account... ✨"):
                        data, status = register_user(
                            reg_username, reg_password)
                    if status == 201:
                        st.success("Registered successfully. Please log in.")
                    else:
                        st.error(data.get("error", "Registration failed."))

        # ----- Login tab -----
        with tab_login:
            log_username = st.text_input("Username", key="log_user")
            log_password = st.text_input(
                "Password", type="password", key="log_pw2"
            )
            if st.button("Login"):
                if not log_username or not log_password:
                    st.error("Username and password required.")
                else:
                    with st.spinner("Signing you in... 🔑"):
                        data, status = login_user(log_username, log_password)
                    if status == 200:
                        st.session_state.user = data["user"]
                        st.success(
                            f"Welcome, {st.session_state.user['username']}!")
                    else:
                        st.error(data.get("error", "Login failed."))

        # ----- Forgot Password tab -----
        with tab_forgot:
            st.write("Reset your password if you’ve forgotten it.")
            fp_username = st.text_input("Username", key="fp_user")
            fp_new = st.text_input(
                "New password", type="password", key="fp_new")
            fp_confirm = st.text_input(
                "Confirm new password", type="password", key="fp_conf"
            )

            if st.button("Reset Password"):
                if not fp_username or not fp_new or not fp_confirm:
                    st.error("All fields are required.")
                elif fp_new != fp_confirm:
                    st.error("New password and confirmation do not match.")
                else:
                    with st.spinner("Resetting password... 🔐"):
                        data, status = forgot_password(fp_username, fp_new)
                    if status == 200:
                        st.success(
                            data.get("message", "Password reset successfully."))
                    else:
                        st.error(data.get("error", "Password reset failed."))

    else:
        st.write(f"**Logged in as:** {st.session_state.user['username']}")
        if st.button("Logout"):
            st.session_state.user = None
            st.success("Logged out.")


# ---------- Main content ----------
if st.session_state.user is None:
    # ---------------- Landing page (logged out) ----------------
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        # Heading (single line)
        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:2.2rem;
                font-weight:750;
                color:#012a4a;
                margin-top:0.2rem;
                margin-bottom:0.3rem;">
                Welcome to AI-Powered Note Management System
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Subtitle
        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:1.05rem;
                color:#355070;
                margin-top:0.1rem;
                margin-bottom:1.0rem;">
                Seamlessly manage your ideas with an AI-powered notes system.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Floating hero illustration
        hero_html = get_hero_image_html("hero_notes.png", width=480)
        st.markdown(hero_html, unsafe_allow_html=True)

        # Bottom guidance text
        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:0.92rem;
                color:#6c757d;
                margin-top:0.8rem;">
                Please log in or register from the sidebar to use the notes system.
            </div>
            """,
            unsafe_allow_html=True,
        )

else:
    # ---------------- Logged-in dashboard ----------------
    user_id = st.session_state.user["user_id"]

    st.title("📝 AI-powered Notes Management System")

    # Two columns: left wide, right narrow
    col_left, col_right = st.columns([3, 1], gap="large")

    # ===== Left: AI Chat + CRUD =====
    with col_left:
        st.subheader("😊 Chat with Your Notes Assistant")

        query = st.text_area(
            "Type a natural language request (create, read, update, delete, list, help):",
            height=120,
            placeholder="Type your request here...",
        )

        ai_loading_placeholder = st.empty()

        if st.button("Send to AI"):
            if not query.strip():
                st.warning("Please enter a message.")
            else:
                ai_loading_placeholder.markdown(
                    '<div class="ai-loading">🤖 Thinking about your request...</div>',
                    unsafe_allow_html=True,
                )
                with st.spinner("Talking to your AI assistant..."):
                    data, status = send_nl_query(user_id, query)
                ai_loading_placeholder.empty()

                if status != 200:
                    st.error(data.get("error", "Something went wrong."))
                else:
                    result = data.get("result", {})

                    if "error" in result:
                        st.error(result["error"])
                    elif "note" in result:
                        note = result["note"]
                        st.success(result.get("message", "Success"))
                        render_single_note(note)
                    elif "notes" in result:
                        notes = result["notes"]
                        if not notes:
                            st.info(result.get("message", "No notes found."))
                        else:
                            if "message" in result:
                                st.success(result["message"])
                            for n in notes:
                                render_single_note(n)
                    elif "message" in result:
                        st.success(result["message"])
                    else:
                        st.info("No result returned.")

        st.markdown("---")
        st.markdown("### 📊 Manually Edit Your Notes")

        tab_create, tab_update, tab_delete = st.tabs(
            ["Create Note", "Update Note", "Delete Note"]
        )

        # ---- CREATE ----
        with tab_create:
            st.subheader("➕ Create a New Note")
            new_topic = st.text_input("Topic", key="create_topic")
            new_message = st.text_area("Message", key="create_message")
            if st.button("Create Note (Manual)"):
                if not new_topic or not new_message:
                    st.error("Topic and Message are required.")
                else:
                    nl_text = f"Create a note about {new_topic} that says {new_message}"
                    with st.spinner("Creating note... ✏️"):
                        data, status = send_nl_query(user_id, nl_text)
                    if status == 200:
                        result = data.get("result", {})
                        if "error" in result:
                            st.error(result["error"])
                        elif "note" in result:
                            st.success(result.get("message", "Note created."))
                            render_single_note(result["note"])
                        else:
                            st.info("Note created.")
                    else:
                        st.error(data.get("error", "Error creating note."))

        # ---- UPDATE ----
        with tab_update:
            st.subheader("✏️ Update Existing Note")
            note_data, _ = fetch_notes(user_id)
            notes = note_data.get("notes", [])
            note_map = {
                f"#{n['note_id']} - {n['topic']}": n["note_id"] for n in notes
            }

            if notes:
                selected_label = st.selectbox(
                    "Select a note to update:",
                    list(note_map.keys()),
                )
                selected_id = note_map[selected_label]
                updated_message = st.text_area(
                    "New message (leave blank to keep same):", key="update_message"
                )
                updated_topic = st.text_input(
                    "New topic (leave blank to keep same):", key="update_topic"
                )

                if st.button("Update Note"):
                    if not updated_message and not updated_topic:
                        st.error(
                            "Provide at least a new topic or a new message.")
                    else:
                        if updated_message and updated_topic:
                            nl_text = (
                                f"Change the topic of note {selected_id} to "
                                f"{updated_topic} with message {updated_message}"
                            )
                        elif updated_topic:
                            nl_text = (
                                f"Change the topic of note {selected_id} to {updated_topic}"
                            )
                        else:
                            nl_text = (
                                f"Update note {selected_id} and say {updated_message}"
                            )

                        with st.spinner("Updating note... ✏️"):
                            data, status = send_nl_query(user_id, nl_text)

                        if status == 200:
                            result = data.get("result", {})
                            if "error" in result:
                                st.error(result["error"])
                            elif "note" in result:
                                st.success(result.get(
                                    "message", "Note updated."))
                                render_single_note(result["note"])
                            else:
                                st.info("Update completed.")
                        else:
                            st.error(data.get("error", "Update failed."))
            else:
                st.info("You have no notes to update.")

        # ---- DELETE ----
        with tab_delete:
            st.subheader("🗑️ Delete Note")
            note_data, _ = fetch_notes(user_id)
            notes = note_data.get("notes", [])
            note_map = {
                f"#{n['note_id']} - {n['topic']}": n["note_id"] for n in notes
            }

            if notes:
                del_label = st.selectbox(
                    "Select a note to delete:",
                    list(note_map.keys()),
                )
                del_id = note_map[del_label]

                if st.button("Delete Note"):
                    nl_text = f"Delete note {del_id}"
                    with st.spinner("Deleting note... 🗑️"):
                        data, status = send_nl_query(user_id, nl_text)
                    if status == 200:
                        result = data.get("result", {})
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success(result.get("message", "Note deleted."))
                            if "deleted_note_id" in result:
                                st.write(
                                    f"Deleted note ID: {result['deleted_note_id']}")
                    else:
                        st.error(data.get("error", "Delete failed."))
            else:
                st.info("No notes available to delete.")

    # ===== Right: Your Notes =====
    with col_right:
        st.markdown(
            '<h3 class="your-notes-header">📚 Your Notes</h3>',
            unsafe_allow_html=True,
        )
        data, status = fetch_notes(user_id)
        if status == 200:
            notes = data.get("notes", [])
            if not notes:
                st.info("No notes yet. Create your first one!")
            else:
                for n in notes:
                    render_single_note(n)
        else:
            st.error(data.get("error", "Could not load notes."))
