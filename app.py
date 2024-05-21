import json
from flask import Flask
import psycopg2
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter, make_wsgi_app, Summary

app = Flask(__name__)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

REQUEST_TIME = Summary(
    "flask_request_processing_seconds", "Time spent processing request"
)
REQUEST_COUNT = Counter("flask_request_counter_flask", "Number of requests")

host = os.environ["DB_HOST"]
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
database = os.environ["DB_NAME"]


@REQUEST_TIME.time()
@app.route("/")
def hello_world():
    REQUEST_COUNT.inc()
    return "--------Hello, Docker!!!!"


@REQUEST_TIME.time()
@app.route("/widgets")
def get_widgets():
    with psycopg2.connect(
        host=host, user=user, password=password, database=database
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM widgets")
            row_headers = [x[0] for x in cur.description]
            results = cur.fetchall()
    conn.close()

    json_data = [dict(zip(row_headers, result)) for result in results]
    return json.dumps(json_data)


@REQUEST_TIME.time()
@app.route("/initdb")
def db_init():
    with psycopg2.connect(
        host=host, user=user, password=password, database=database
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS widgets")
            cur.execute(
                "CREATE TABLE widgets (name VARCHAR(255), description VARCHAR(255))"
            )
    conn.close()

    return "init database"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
