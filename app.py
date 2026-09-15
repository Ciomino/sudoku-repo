from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import time

app = Flask(__name__, static_folder='static')
DB_PATH = os.environ.get('DB_PATH', '/data/sudoku.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            seconds INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/complete', methods=['POST'])
def complete():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()[:40]
    difficulty = data.get('difficulty')
    try:
        seconds = int(data.get('seconds', 0))
    except (TypeError, ValueError):
        seconds = 0

    if not name or difficulty not in ('easy', 'medium', 'hard') or seconds <= 0:
        return jsonify({'error': 'dati non validi'}), 400

    conn = get_db()
    conn.execute(
        'INSERT INTO completions (name, difficulty, seconds, created_at) VALUES (?, ?, ?, ?)',
        (name, difficulty, seconds, int(time.time()))
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/leaderboard')
def leaderboard():
    conn = get_db()
    rows = conn.execute('''
        SELECT name, COUNT(*) AS levels_completed, AVG(seconds) AS avg_seconds
        FROM completions
        GROUP BY name
        ORDER BY levels_completed DESC, avg_seconds ASC
    ''').fetchall()
    conn.close()
    result = [
        {
            'name': r['name'],
            'levels_completed': r['levels_completed'],
            'avg_seconds': round(r['avg_seconds'])
        }
        for r in rows
    ]
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
