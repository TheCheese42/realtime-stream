import os
from pathlib import Path

import dotenv
from flask import Flask, jsonify, render_template, request
from mysql.connector import Error as ConnectorError

from .database import Database

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


INTERNAL_ERROR = jsonify({"error": "An internal error occurred."}), 500


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/c", methods=["POST"])
def create_output():
    try:
        uuid = DB.create_output()
    except ConnectorError:
        return INTERNAL_ERROR

    return jsonify(
        {"message": "New output created successfully", "uuid": uuid}
    ), 201


@app.route("/a/<str:uuid>", methods=["PATCH"])
def append_to_output(uuid):
    data = request.get_json()

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


@app.route("/d/<str:uuid>", methods=["DELETE"])
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
