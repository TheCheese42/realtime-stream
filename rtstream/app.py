import os
import threading
from pathlib import Path

import dotenv
from flask import Flask, jsonify, make_response, render_template, request
from mysql.connector import Error as ConnectorError

try:
    from database import Database
    from delete_daemon import delete_daemon
except ModuleNotFoundError:
    from .database import Database
    from .delete_daemon import delete_daemon

app = Flask(__name__)


dotenv.load_dotenv(Path(__file__).parent.parent / ".env")
host = os.getenv("MYSQL_HOST")
user = os.getenv("MYSQL_USERNAME")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")
port = os.getenv("MYSQL_PORT")


def malformed_dotenv(missing_key: str):
    raise RuntimeError(f"Malformed .env: Missing key '{missing_key}'")


if host is None:
    malformed_dotenv("MYSQL_HOST")
if user is None:
    malformed_dotenv("MYSQL_USERNAME")
if password is None:
    malformed_dotenv("MYSQL_PASSWORD")
if database is None:
    malformed_dotenv("MYSQL_DATABASE")


DB = Database(
    host=host,
    user=user,
    password=password,
    database=database,
    port=port or "3306",
)


thread = threading.Thread(target=delete_daemon, daemon=True, args=(DB,))
thread.start()


with app.app_context():
    INTERNAL_ERROR = jsonify({"error": "An internal error occurred."}), 500


@app.route("/")
def index() -> str:
    return render_template("index.html", host=request.host)


@app.route("/c", methods=["POST"])
def create_output():
    try:
        uuid = DB.create_output()
    except ConnectorError:
        return INTERNAL_ERROR

    data = request.get_data().decode("utf-8")
    if data:
        try:
            DB.append_to_output(uuid, data)
        except ConnectorError:
            return INTERNAL_ERROR

    return uuid, 201


@app.route("/a/<uuid>", methods=["PATCH"])
def append_to_output(uuid):
    data = request.get_data().decode("utf-8")

    try:
        if not DB.has_output(uuid):
            return jsonify({"error": "Output doesn't exist"}), 404
    except ConnectorError:
        return INTERNAL_ERROR

    try:
        DB.append_to_output(uuid, data)
    except ConnectorError:
        return INTERNAL_ERROR

    try:
        DB.update_timestamp(uuid)
    except ConnectorError:
        pass  # Unlikely and unimportant.

    return jsonify({"message": "Output appended successfully"}), 200


@app.route("/d/<uuid>", methods=["DELETE"])
def delete_output(uuid):
    try:
        if not DB.has_output(uuid):
            return jsonify({"error": "Output doesn't exist"}), 404
    except ConnectorError:
        return INTERNAL_ERROR

    try:
        DB.delete_output(uuid)
    except ConnectorError:
        return INTERNAL_ERROR

    return jsonify({"message": "Output deleted successfully"}), 200


@app.route("/g/<uuid>")
def get_output(uuid):
    try:
        if not DB.has_output(uuid):
            return jsonify({"error": "Output doesn't exist"}), 404
    except ConnectorError:
        return INTERNAL_ERROR

    try:
        output = DB.get_output(uuid)
    except ConnectorError:
        return INTERNAL_ERROR

    return output, 200


@app.route("/v/<uuid>")
def webview(uuid):
    return render_template("webview.html", uuid=uuid)


@app.route("/script")
def script():
    response = make_response(
        (Path(__file__).parent / "rts.sh").read_text("utf-8").replace(
            "{host}", request.host, 1
        ),
        200
    )
    response.mimetype = "text/plain"
    return response
