import time
import uuid
from tempfile import mkdtemp
from flask import Flask, render_template, request, session, redirect, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from cs50 import SQL 
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# enable sessions where they are stored in the filesystem, under /tmp
app.config['SESSION_FILE_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///chat.db")

socketio = SocketIO(app)

def render_template_login(template_name_or_list, **context):
    """ Helper that adds the 'logged_in' param automatically """
    context["logged_in"] = "user_id" in session
    return render_template(template_name_or_list, **context)

@app.route("/")
def index():
    if not session:
        return redirect("/login")

    rooms = db.execute("SELECT id, nickname, room_address, created_time FROM rooms order by created_time DESC")

    return render_template_login("index.html", rooms=rooms)


@app.route("/rooms", methods=["GET", "POST"])
def room_route():
    if not session:
        return redirect("/login")
    
    if request.method == "POST":

        # Create the room

        if not request.form.get("roomname"):
            flash("Room name required")
            return render_template_login("create_room.html")

        utc_time = int(time.time())
        unique_id = uuid.uuid4().hex
        
        res = db.execute("INSERT INTO rooms (nickname, room_address, created_time) VALUES (?, ?, ?)", request.form.get("roomname"), unique_id, utc_time)

        if not res:
            flash("Something went wrong")
            return render_template_login("create_room.html")
        return redirect(f"/rooms?room={unique_id}")
    else:
        room = None
        if request.args.get("room"):
            room = db.execute("SELECT nickname, room_address, created_time FROM rooms WHERE room_address = ?", request.args.get("room"))
        if not room:
            return render_template_login("create_room.html")
        return render_template_login("room.html", room=room[0])


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            flash("Username required")
            return render_template_login("login.html") # error

        if not request.form.get("password"):
            flash("Password required")
            return render_template_login("login.html") # error

        # find the user
        users = db.execute("SELECT id, username, password_hash FROM users WHERE username = ?", request.form.get("username"))

        if not users or len(users) != 1:
            # return an error if not found
            flash("Invalid username / password")
            return render_template_login("login.html") # error

        user = users[0]

        # check if the password matches
        if check_password_hash(pwhash=user["password_hash"], password=request.form.get("password")):
            # the password matched
            session["user_id"] = user["id"] # OK
            session["username"] = user["username"]
            return redirect("/")
        else:
            # wrong password
            flash("Invalid username / password")
            return render_template_login("login.html") # error
    else:
        return render_template_login("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            flash("Username required")
            return render_template_login("register.html") # error

        if not request.form.get("password"):
            flash("Password required")
            return render_template_login("register.html") # error

        if not request.form.get("confirmation") :
            flash("Password required")
            return render_template_login("register.html") # error

        if request.form.get("confirmation") != request.form.get("password"):
            flash("Passwords must match")
            return render_template_login("register.html") # error

        # check if username is unique
        rows = db.execute("SELECT id, username FROM users WHERE username = ?", request.form.get("username"))
        if rows:
            flash("Username is taken")
            return render_template_login("register.html") # error
        
        # OK to insert the user
        result = db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    request.form.get("username"),
                    generate_password_hash(request.form.get("password")))
        if not result:
            flash("Something went wrong")
            return render_template_login("register.html") # error
        return redirect("/login")
    else:
        return render_template_login("register.html")


@socketio.on('connect')
def handle_connect(auth):
    """ Connect the websocket
        Check the auth for credentials to ensure they are allowed to connect.
    """
    print("connected", auth, request.sid, session)
    return True


@socketio.on("disconnect")
def handle_disconnect():
    print("disconnected", request.sid)


@socketio.on('join')
def on_join(data):
    """ Allows a user to join a room
        This allows them to get messages sent to that 'room',
        and also to send messages to all users who are also part of the room
    """
    print("on join")
    if "username" in session:
        username = session["username"]
        user_id = session["user_id"]
        room = data["room"]

        # find the room in the database
        rows = db.execute("SELECT id FROM rooms WHERE room_address = ?", room)
        room_id = rows[0]["id"]

        # update the database to set the user as in the room
        # check if they are already in the room, clear out any old room data
        rows = db.execute("DELETE FROM room_users WHERE user_id = ? AND room_id = ?", user_id, room_id)
        # they are not in the room already
        rows = db.execute("INSERT INTO room_users (user_id, room_id, active_time) VALUES (?, ?, ?)",
                            user_id, room_id, int(time.time()))

        print("join room", room)
        join_room(room) # room's are managed by the library
        emit("server_room", {"message": f"{username} has entered the room"}, to=room)

        # send updated participants list
        room_users = db.execute("SELECT username, active_time FROM room_users JOIN users on room_users.user_id = users.id WHERE room_id = ?", room_id)
        emit("server_participants", {"participants": room_users}, to=room)

    else:
        print("join failed (not logged in)")
        emit("server_room", {"message": "join failed"}, to=request.sid)


@socketio.on('leave')
def on_leave(data):
    """ The user has left a room """

    username = data["username"]
    room = data["room"]

    print(f"{username} has left room: {room}")

    leave_room(room) # room's are managed by the library
    emit("server_room", {"message": f"{username} has left the room",}, to=room)


@socketio.on("client_message")
def handle_client_message(data):
    print("received client_message: ", data)
    try:
        # expect a room
        room = data["room"]
        # expect a message
        message = data["message"]

        if "username" in session:
            username = session["username"]
            # only allow logged in users to post messages
            print("sending message")
            emit("server_message", {"message": message, "username": username, "room": room}, to=room)
        else:
            print("failed to send message")
    except Exception as ex:
        print(repr(ex))
        emit("server_room", {"message": "failed to send message"}, to=request.sid)


@socketio.on("client_heartbeat")
def handle_client_heartbeat(data):
    """
    The client sends a heartbeat every 5sec to let the server know it is still active.
    When a heartbeat is received, the db will be the active participants list.
    """
    if "user_id" in session:
        # only allow if the user is logged in
        room = data["room"]
        room_id = db.execute("SELECT id FROM rooms WHERE room_address = ?", room)[0]["id"]
        user_id = session["user_id"]
        db.execute("UPDATE room_users SET active_time = ? WHERE user_id = ? AND room_id = ?", int(time.time()), user_id, room_id)
        
        # send updated participants list
        room_users = db.execute("SELECT username, active_time FROM room_users JOIN users on room_users.user_id = users.id WHERE room_id = ?", room_id)
        emit("server_participants", {"participants": room_users}, to=room)


if __name__ == '__main__':
    #referenced https://flask-socketio.readthedocs.io/en/latest/getting_started.html#initialization 
    socketio.run(app, host="0.0.0.0", debug=True)
