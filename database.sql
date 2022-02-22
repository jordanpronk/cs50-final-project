
-- create the users table
CREATE table users (
    id INTEGER,
    username TEXT not null,
    password_hash TEXT not null,
    PRIMARY KEY (id)
);

-- create a unique index on username, for faster lookup
CREATE UNIQUE INDEX username on users (username);

-- create the rooms table, which are the available chat rooms
CREATE table rooms (
    id INTEGER,
    nickname TEXT NOT NULL,
    room_address TEXT NOT NULL,
    created_time INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX room_address on rooms (room_address);

-- create a table for keeping track of which users are in a room
CREATE table room_users (
    id INTEGER,
    user_id INTEGER,
    room_id INTEGER,
    active_time INTEGER, -- last active time
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE INDEX user_id on room_users (user_id);
CREATE INDEX room_id on room_users (room_id);

