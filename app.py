import os
from datetime import datetime
from flask import Flask, send_from_directory

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database models

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev_secret_key"),
        SQLALCHEMY_DATABASE_URI=(
            os.environ.get("DATABASE_URL")
            or f"sqlite:///{os.path.join(BASE_DIR, 'chat.db')}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return User.query.get(user_id)

    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    @app.route("/")
    def index():
        if current_user():
            return redirect(url_for("chat"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user():
            return redirect(url_for("chat"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")

            if not username:
                flash("Iltimos, foydalanuvchi nomini kiriting.")
            elif not password:
                flash("Iltimos, parol kiriting.")
            elif password != confirm:
                flash("Parollar mos emas.")
            elif User.query.filter_by(username=username).first():
                flash("Bu foydalanuvchi nomi allaqachon ishlatilgan.")
            else:
                user = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                )
                db.session.add(user)
                db.session.commit()
                flash("Ro'yxatdan muvaffaqiyatli o'tdingiz. Iltimos, tizimga kiring.")
                flash(f"Sizning foydalanuvchi IDingiz: {user.id}. Uni do'stlar qo'shishda ishlatishingiz mumkin.")
                return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user():
            return redirect(url_for("chat"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter_by(username=username).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Foydalanuvchi nomi yoki parol noto'g'ri.")
            else:
                session.clear()
                session["user_id"] = user.id
                return redirect(url_for("chat"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/google4d8d977b196abeb8.html")
    def google_verification():
        return send_from_directory(os.path.join(BASE_DIR, 'static'), 'google4d8d977b196abeb8.html')

    @app.route("/chat")
    def chat():
        user = current_user()
        if not user:
            return redirect(url_for("login"))

        # Only show users that have been added as friends.
        users = (
            User.query
            .join(Friend, Friend.friend_id == User.id)
            .filter(Friend.user_id == user.id)
            .order_by(User.username)
            .all()
        )
        return render_template("chat.html", users=users)

    @app.route("/add_friend", methods=["POST"])
    def add_friend():
        user = current_user()
        if not user:
            abort(401)

        friend_id = request.form.get("friend_id", "").strip()
        if not friend_id:
            flash("Iltimos, do'st ID sini kiriting.")
            return redirect(url_for("chat"))

        try:
            friend_id = int(friend_id)
        except ValueError:
            flash("Noto'g'ri ID kiritildi.")
            return redirect(url_for("chat"))

        if friend_id == user.id:
            flash("O'zingizni do'st sifatida qo'sha olmaysiz.")
            return redirect(url_for("chat"))

        friend = User.query.get(friend_id)
        if not friend:
            flash("Bunday foydalanuvchi topilmadi.")
            return redirect(url_for("chat"))

        existing = Friend.query.filter_by(user_id=user.id, friend_id=friend.id).first()
        if existing:
            flash("Bu foydalanuvchi allaqachon do'stlar ro'yxatida.")
            return redirect(url_for("chat"))

        # Create mutual friendship so both users can message each other.
        db.session.add(Friend(user_id=user.id, friend_id=friend.id))
        db.session.add(Friend(user_id=friend.id, friend_id=user.id))
        db.session.commit()

        flash(f"{friend.username} do'stlar ro'yxatiga qo'shildi.")
        return redirect(url_for("chat"))

    @app.route("/send", methods=["POST"])
    def send_message():
        user = current_user()
        if not user:
            abort(401)

        # Determine if the request expects JSON (AJAX) or a normal form submit.
        wants_json = (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.accept_mimetypes.best == "application/json"
        )

        def json_error(msg, status=400):
            if wants_json:
                return {"success": False, "error": msg}, status
            flash(msg)
            return redirect(url_for("chat"))

        text = request.form.get("text", "").strip()
        recipient_id = request.form.get("recipient_id")

        if not text:
            return json_error("Iltimos, xabar yozing.")

        if not recipient_id:
            return json_error("Iltimos, foydalanuvchi tanlang.")

        try:
            recipient_id = int(recipient_id)
        except ValueError:
            return json_error("Noto'g'ri foydalanuvchi tanlandi.")

        recipient = User.query.get(recipient_id)
        if not recipient:
            return json_error("Tanlangan foydalanuvchi topilmadi.")

        # Validate that the recipient is in the current user's friends list.
        if not Friend.query.filter_by(user_id=user.id, friend_id=recipient.id).first():
            return json_error("Siz bu foydalanuvchini do'stlar ro'yxatiga qo'shmagansiz. Avval uni qo'shing.")

        message = Message(
            sender_id=user.id,
            recipient_id=recipient.id,
            text=text,
        )
        db.session.add(message)
        db.session.commit()

        if wants_json:
            return {"success": True}
        return redirect(url_for("chat"))

    @app.route("/messages")
    def messages():
        user = current_user()
        if not user:
            abort(401)

        # Only return private messages (no public broadcasts)
        msgs = (
            Message.query
            .filter(
                Message.recipient_id.is_not(None),
                ((Message.recipient_id == user.id) | (Message.sender_id == user.id)),
            )
            .order_by(Message.created_at.asc())
            .all()
        )

        data = []
        for m in msgs:
            data.append(
                {
                    "id": m.id,
                    "text": m.text,
                    "sender": m.sender.username,
                    "sender_id": m.sender_id,
                    "recipient": m.recipient.username if m.recipient else None,
                    "recipient_id": m.recipient_id,
                    "time": m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return {"messages": data}

    return app


# Database models


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    messages_sent = db.relationship(
        "Message", back_populates="sender", foreign_keys="Message.sender_id"
    )
    messages_received = db.relationship(
        "Message", back_populates="recipient", foreign_keys="Message.recipient_id"
    )


class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", foreign_keys=[user_id], backref="friend_links")
    friend = db.relationship("User", foreign_keys=[friend_id])

    __table_args__ = (
        db.UniqueConstraint("user_id", "friend_id", name="uq_user_friend"),
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship("User", back_populates="messages_sent", foreign_keys=[sender_id])
    recipient = db.relationship("User", back_populates="messages_received", foreign_keys=[recipient_id])



if __name__ == "__main__":
    app = create_app()
    # Allow overriding host/port via environment variables for easy deployment.
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

    app.run(host=host, port=port, debug=debug)


application = create_app()
app = create_app()
application = app


@app.route('/google4d8d977b196abeb8.html')
def verify():
    return send_from_directory('static', 'google4d8d977b196abeb8.html')