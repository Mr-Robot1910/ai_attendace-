from flask import Flask
from .database import init_db
import threading


def create_app():
    app = Flask(__name__)
    try:
        from config import SECRET_KEY
        app.secret_key = SECRET_KEY
    except ImportError:
        app.secret_key = 'ai_attendance_super_secret_key_2024'

    with app.app_context():
        init_db()

    # Pre-load MTCNN + FaceNet in background — delayed so the server
    # fully starts and can respond to requests before TF loads
    def _warm():
        import time
        time.sleep(8)   # give Flask time to finish starting
        from . import face_module as fm
        fm.warm_up()
    threading.Thread(target=_warm, daemon=True).start()

    from .routes import routes
    app.register_blueprint(routes)

    return app
