"""
app.py — Flask application factory.

Usage:
  python app.py                    # run dev server on :5001
  flask --app app shell            # interactive shell with app context
  flask --app app init-db          # (re)create all tables
"""
import os
import click
from flask import Flask

from config import get_config
from models import db


def create_app(config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config or get_config())

    # ── Extensions ──────────────────────────────────────────────────
    db.init_app(app)

    # ── Blueprints ───────────────────────────────────────────────────
    from apps.dashboard.routes   import dashboard_bp
    from apps.assessments.routes import assessments_bp
    from apps.reporting.routes   import reporting_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(reporting_bp)

    # ── CLI commands ─────────────────────────────────────────────────
    @app.cli.command("init-db")
    def init_db_command():
        """Drop and recreate all tables."""
        with app.app_context():
            db.drop_all()
            db.create_all()
        click.echo("Database initialised.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Create a demo assessment seeded with iCIMS sample data."""
        import requests
        with app.app_context():
            db.create_all()
        base = "http://localhost:5001"
        # Create assessment
        r = requests.post(f"{base}/assessments/", data={
            "client_name": "iCIMS TechOps · Apr 2026",
            "created_by": "Marc Harfeld",
        }, allow_redirects=False)
        location = r.headers.get("Location", "")
        assessment_id = location.rstrip("/").split("/")[-2] if location else None
        if assessment_id:
            requests.post(f"{base}/assessments/api/{assessment_id}/seed")
            click.echo(f"Demo assessment created: id={assessment_id}")
        else:
            click.echo("Could not parse assessment id from redirect. Start the server first.")

    # ── Auto-create tables on startup (dev only) ─────────────────────
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\n{'='*52}")
    print(f"  Templatinator · vCISO Assessment Platform")
    print(f"  http://localhost:{port}")
    print(f"  DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"{'='*52}\n")
    app.run(debug=True, port=port)
