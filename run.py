from app import create_app, socketio
import os

# Explicitly use development configuration with SQLite
app = create_app('development')

if __name__ == '__main__':
    print(f"Starting AGV Finance server with database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)