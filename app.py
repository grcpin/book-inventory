from flask import Flask, request, jsonify
import sqlite3
import whisper
import os

app = Flask(__name__)

model = whisper.load_model("base")

DB_FILE = "books.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            year TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/dictate", methods=["POST"])
def dictate():
    if "audio" not in request.files:
        return jsonify({"error": "Aucun fichier audio reçu"}), 400
    
    audio_file = request.files["audio"]
    file_path = "temp.wav"
    audio_file.save(file_path)
    
    result = model.transcribe(file_path)
    os.remove(file_path)
    
    text = result["text"]
    
    # Simple parsing pour chercher un format "Titre: ... Auteur: ... Année: ..."
    parts = text.split(" ")
    title = " ".join(parts[:3]) if len(parts) > 3 else text  # On prend les 3 premiers mots comme titre
    author = " ".join(parts[3:5]) if len(parts) > 5 else "Inconnu"
    year = parts[-1] if parts[-1].isdigit() else "N/A"
    
    # Sauvegarde dans la base
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", (title, author, year))
    conn.commit()
    conn.close()
    
    return jsonify({"title": title, "author": author, "year": year})

@app.route("/books", methods=["GET"])
def get_books():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()
    
    return jsonify([{ "id": b[0], "title": b[1], "author": b[2], "year": b[3] } for b in books])

if __name__ == "__main__":
    app.run(debug=True)
