import sqlite3
from flask import Flask, request, redirect
from flask import render_template
import requests
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "static/covers"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def hello():
    conn = sqlite3.connect("music.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM albums")
    rows = cur.fetchall()
    conn.close()

    return render_template("albums.html", albums=rows)

@app.route("/add", methods=["POST"])
def add_album():

    title = request.form["title"]
    artist = request.form["artist"]
    year = request.form["year"]

    file = request.files.get("cover")
    cover_url = request.form.get("cover_url")
    cover_path = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        cover_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(cover_path)

    elif cover_url:
        image_data = requests.get(cover_url).content
        filename = f"{uuid.uuid4().hex}.jpg"
        cover_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        with open(cover_path, "wb") as f:
            f.write(image_data)

    else:
        search_url = f"https://itunes.apple.com/search?term={title}+{artist}&entity=album&limit=1"
        response = requests.get(search_url)
        data = response.json()

        if data["resultCount"] > 0:
            auto_cover = data["results"][0]["artworkUrl100"].replace("100x100", "600x600")
            image_data = requests.get(auto_cover).content
            filename = f"{uuid.uuid4().hex}.jpg"
            cover_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            with open(cover_path, "wb") as f:
                f.write(image_data)
        else:
            cover_path = "static/covers/default.jpg"

    conn = sqlite3.connect("music.db")
    cur = conn.cursor()

    sql = '''INSERT INTO albums(title, artist, year, cover)
             VALUES(?, ?, ?, ?)'''

    cur.execute(sql, [title, artist, year, cover_path])
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/delete/<int:albumID>")
def delete_album(albumID):

    conn = sqlite3.connect("music.db")
    cur = conn.cursor()

    sql = '''DELETE FROM albums WHERE albumID = ?'''
    cur.execute(sql, [albumID])
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/rate/<int:albumID>", methods=["POST"])
def update_rating(albumID):
    rating = request.form["rating"]

    conn = sqlite3.connect("music.db")
    cur = conn.cursor()

    sql = '''UPDATE albums SET rating = ? WHERE albumID = ?'''
    cur.execute(sql, [rating, albumID])
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/search")
def get_album():
    q = request.args.get("q")

    url = f"https://itunes.apple.com/search?term={q}&entity=album&limit=10&attribute=albumTerm"
    response = requests.get(url)
    data = response.json()

    return render_template("search_results.html", albums=data["results"])
