# Realtime Stream

An application to share terminal output streams.

## Hosting

First, clone and install the requirements.

```sh
git clone https://github.com/TheCheese42/realtime-stream
cd realtime-stream
python -m venv .venv
source .venv/bin/activate  # Linux and MacOS
.venv/Scripts/activate.ps1  # Windows
pip install -r requirements.txt
```

\
Then, add a .env file to the root directory. The content should be as follows:

```toml
FLASK_APP = "rtstream/app.py"

# The following are required when using MySQL
MYSQL_HOST = "<MYSQL_DB_URL_HERE>"
MYSQL_PORT = "3306"  # This is the standard MySQL port
MYSQL_USERNAME = "<MYSQL_USERNAME_HERE>"
MYSQL_PASSWORD = "<MYSQL_PASSWORD_HERE>"
MYSQL_DATABASE = "<MYSQL_DATABASE_NAME_HERE>"

# The following are required when using SQLite. Do NOT add them otherwise!
RTS_USE_SQLITE = "1"
RTS_SQLITE_PATH = "rtstream.db"
```

## Usage

This tool is intended to be used with a terminal binary like cURL or the `rts` script to redirect terminal output to the webserver, making it accessible for everyone with the link. Streams can be seen using the `/g` endpoint or in the webview, using the `/v` endpoint (also usable through the index page).

### Databases

The application can either connect to a MySQL or an SQLite database. Both can be initialized using the `setup_db.py` script:

```sh
python setup_db.py
```

The script reads everything it needs from the `.env` file, including wether it should use MySQL or SQLite.

### The `rts` script

The `rts` script can be found at the `/script` path of the webserver. It handles sending the cURL requests to the hostname it was downloaded from. It is a **bash** script, it does **not** work on regular Windows shells.

This install instruction can also be found on the index page, with the correct url.

```sh
curl "http://doma.in/script" > ~/.local/bin/rts && chmod +x ~/.local/bin/rts
```

It can be used like this:

```sh
neofetch | rts
```

This prints the UUID of the newly created stream to the stdout. It also prints the piped output. To append to an existing stream, pass that as an argument to `rts`.

```sh
neofetch | rts ABC123
```

### The webview

Instead of fetching stream output from the terminal, it can also be viewed from the browser. The webview at `/v/<uuid>` will refresh automatically. It can also be accessed by entering the UUID into the dedicated input field at the top of the index page.

### Endpoints

The application has the following REST API endpoints:

#### Create a new output stream

Endpoint: `/c`
HTTP Method: `POST`
Successful response content: The UUID of the newly created output stream.

Examples (cURL):
`curl -X POST http://doma.in/c`
`curl -X POST -d "Initial Data" http://doma.in/c`

#### Append to an output stream

Endpoint: `/a/<uuid>`
HTTP Method: `PATCH`

Example (cURL):
`curl -X PATCH -d "Some new output for the stream" http://doma.in/a/ABC123`

#### Delete an output stream

Endpoint: `/d/<uuid>`
HTTP Method: `DELETE`

Example (cURL):
`curl -X DELETE http://doma.in/d/ABC123`

#### Fetch a stream's full output

Endpoint: `/g/<uuid>`
Successful response content: The full output as plain text.
HTTP Method: `GET`

Example (cURL):
`curl http://doma.in/g/ABC123`
