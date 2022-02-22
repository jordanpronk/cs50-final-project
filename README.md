# Chat
#### Video Demo:  https://youtu.be/Adl-zhJxgQE
#### Description:
The project is a room-based chat application using websockets to broadcast message to all participants in a room.

The backend is using Python, and Flask, with a sqlite3 database. It also makes use of the python-socketio library.

The frontend is using Javascript, and the SocketIO library, as well as bootstrap.

users may sign register for access to the site. Access is only allowed to logged in users. Once the user is logged in they are able to see a list of available chat rooms that they can enter, and they are also able to create a new chat room. Chat rooms can be entered by any user.

Once the user enters a chat room, they are immediately notified by the participants in the chat room. This is done through a websocket event from the server. Once the user establishes the websocket connection with the backend, and they join the room they have selected, the backend queries the database for all active users in the room. The list of users in the room and the last time they were active is sent in the websocket event to the client. It is left up to the client to filter the list of participants based on how long ago they were active in this room. I made this design choice so that there was less dependency on a timeout on the frontend and the backend. The backend simply reports when the users in the room were last active, and the frontend chooses how to display that information to the user.

There is a heartbeat that each client sends to the server periodically via Javascript. This allows the server to keep track of when a user is active in a room. The heartbeat updates the backend database to set the last active time for the user in that particular room. When a heartbeat is performed, the server selects all users in that room and sends it to the client via a websocket event.
An alternative design of not using the database for active users was considered, by forwarding the heartbeat to all connected clients. This was not chosen as it would cause a delay in getting the participants list when first joining a room. It is desirable to immediately access the entire participant list when first joining a room, rather than waiting for all participants to send in their heartbeat.

To keep chat rooms separate, a UUID address is generated for each, which is used to identify it, like an address. The Python-SocketIO library supports rooms, and so this UUID address is used to identify the room to send websocket event messages to. This ensures that messages are only sent to the appropriate users. A UUID was chosen over using the database ID of the room because it would be too easy to guess the address of a room if they are in sequential order. The UUID is included as a GET parameter in the URL (as room=UUID) so that is it easy to send links to friends to join the room.


The main files are:

- application.py
    - Implements the Flask server, its routes, and the websocket routes. The backend logic is defined here.

- chat.db
    - the sqlite database that is used to store the data for users and rooms.

- database.sql
    - this file is the SQL commands to create the database tables and indices

- templates/
    - the HTML templates for the website, which are rendered from application.py.
    - layout.html is the layout for the page, and implements blocks that are implemented by templates which extend it. It also defines the navigation menu.
    - rooms.html is the HTML page for the chat room.
    - login.html is the HTML page for logging in.
    - index.html is the main entrypoint, it lists chat room links and allows the user to create a new chat room.

- static/
    - chat.js is the Javascript that handles chat related events, including websocket connections.
    - index.css is the CSS styling for the site

- requirements.txt
    - contains the required python libraries
    - install with `pip3 install -r requirements.txt`

#### Running:

Run `sqlite3 chat.db < database.sql` to setup the sqlite database

To run you must use `python3 application.py`. There is special setup code in the main that makes the development server work with web sockets.