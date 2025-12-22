import os
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Note
from llm_agent import parse_user_query

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "notes.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "cs5200-secret-key"

db.init_app(app)

# ----------------- DB init -----------------
with app.app_context():
    db.create_all()


# ============ Auth endpoints ============

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 400

    hashed_pw = generate_password_hash(password)
    user = User(username=username, password=hashed_pw)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "invalid credentials"}), 401

    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "login successful", "user": user.to_dict()}), 200


@app.route("/api/forgot_password", methods=["POST"])
def forgot_password():
    """
    Simple 'forgot password' reset.
    User only provides: username + new_password.
    Validation:
      - username and new_password required
      - user must exist
      - new password cannot be the same as the existing password
    """
    data = request.get_json() or {}
    username = data.get("username")
    new_password = data.get("new_password")

    if not username or not new_password:
        return jsonify({"error": "username and new_password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Check if new password is the same as the current one
    if check_password_hash(user.password, new_password):
        return jsonify(
            {"error": "new password cannot be the same as your current (old) password"}
        ), 400

    # Update password
    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "password reset successfully"}), 200


# ============ Helper: perform CRUD based on NoteAction ============

def perform_action(user_id: int, action_obj):
    """
    Handles NoteAction from the LLM.
    Supports fields like:
      - action
      - topic / new_topic / target_topic
      - message / new_message
      - note_id
      - search_query
    """
    action = getattr(action_obj, "action", None)

    topic = (
        getattr(action_obj, "topic", None)
        or getattr(action_obj, "new_topic", None)
        or getattr(action_obj, "target_topic", None)
    )
    message = getattr(action_obj, "message", None) or getattr(
        action_obj, "new_message", None
    )
    note_id = getattr(action_obj, "note_id", None)
    search_query = getattr(action_obj, "search_query", None)

    # CREATE
    if action == "create":
        if not topic or not message:
            return {"error": "For create, both topic and message are required."}

        note = Note(
            user_id=user_id,
            topic=topic,
            message=message,
            last_update=datetime.utcnow(),
        )
        db.session.add(note)
        db.session.commit()
        return {"message": "Note created", "note": note.to_dict()}

    # LIST
    if action == "list":
        notes = Note.query.filter_by(
            user_id=user_id).order_by(Note.last_update.desc())
        return {"notes": [n.to_dict() for n in notes]}

    # READ
    if action == "read":
        query = Note.query.filter_by(user_id=user_id)
        if note_id is not None:
            query = query.filter_by(note_id=note_id)
        if topic:
            query = query.filter(Note.topic.ilike(f"%{topic}%"))
        if search_query:
            like = f"%{search_query}%"
            query = query.filter(
                (Note.topic.ilike(like)) | (Note.message.ilike(like))
            )

        notes = query.order_by(Note.last_update.desc()).all()
        if not notes:
            return {"message": "No matching notes found."}
        return {"notes": [n.to_dict() for n in notes]}

    # UPDATE
    if action == "update":
        query = Note.query.filter_by(user_id=user_id)
        if note_id is not None:
            query = query.filter_by(note_id=note_id)
        elif topic:
            query = query.filter(Note.topic.ilike(f"%{topic}%"))
        else:
            return {"error": "Specify note_id or topic to update."}

        note = query.first()
        if not note:
            return {"error": "Note not found."}

        if message:
            note.message = message
        if topic and topic != note.topic:
            note.topic = topic

        note.last_update = datetime.utcnow()
        db.session.commit()
        return {"message": "Note updated", "note": note.to_dict()}

    # DELETE
    if action == "delete":
        query = Note.query.filter_by(user_id=user_id)
        if note_id is not None:
            query = query.filter_by(note_id=note_id)
        elif topic:
            query = query.filter(Note.topic.ilike(f"%{topic}%"))
        else:
            return {"error": "Specify note_id or topic to delete."}

        note = query.first()
        if not note:
            return {"error": "Note not found."}

        db.session.delete(note)
        db.session.commit()
        return {"message": "Note deleted", "deleted_note_id": note.note_id}

    # HELP
    if action == "help":
        return {
            "message": (
                "You can say things like:\n"
                "- 'Create a note about AI that says I love transformers'\n"
                "- 'Show all my notes'\n"
                "- 'Update note 2 and say exam is on Friday'\n"
                "- 'Delete my note about databases'\n"
            )
        }

    return {"error": f"Unknown action: {action}"}


# ============ Natural language endpoint ============

@app.route("/api/nl_query", methods=["POST"])
def nl_query():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    user_input = data.get("query", "")

    if not user_id:
        return jsonify({"error": "user_id required (login first)."}), 400
    if not user_input:
        return jsonify({"error": "query text required."}), 400

    try:
        action_obj = parse_user_query(user_input)
    except Exception as e:
        return jsonify({"error": f"LLM parsing failed: {str(e)}"}), 500

    result = perform_action(user_id, action_obj)
    return jsonify(
        {
            "parsed_action": action_obj.model_dump(),
            "result": result,
        }
    )


# ============ Basic notes list endpoint ============

@app.route("/api/notes", methods=["GET"])
def list_notes():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    notes = Note.query.filter_by(
        user_id=user_id).order_by(Note.last_update.desc())
    return jsonify({"notes": [n.to_dict() for n in notes]})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
