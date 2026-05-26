"""
Application entry point.

Run with:
    python run.py

Environment variables:
    FLASK_ENV: 'development', 'production', or 'testing'
    FLASK_DEBUG: 1 for auto-reload, 0 to disable
    FLASK_PORT: Port to run on (default 5000)
"""

import os
from app import create_app, db

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))


# CLI commands for database management
@app.cli.command()
def init_db_command():
    """Initialize the database."""
    print("Creating tables...")
    db.create_all()
    print("✓ Database initialized")


@app.cli.command()
def seed_db_command():
    """Seed database with sample data."""
    from scripts.seed_db import seed_database
    seed_database()
    print("✓ Database seeded with sample data")


if __name__ == '__main__':
    # Debug mode and port from environment
    debug = os.getenv('FLASK_DEBUG', True)
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"\n{'='*60}")
    print(f"Starting HYA Volunteer Management System")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {debug}")
    print(f"Server running on: http://localhost:{port}")
    print(f"{'='*60}\n")
    
    app.run(debug=debug, port=port)