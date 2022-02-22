
var socket;

var thisUser;
var thisRoom;
var thisHeartbeatInterval;

document.addEventListener("DOMContentLoaded", function() {
    
    const sendButton = document.querySelector("#send-btn");
    const messageInput = document.querySelector("#message-input");
    const messageInputForm = document.querySelector("#message-input-form");
    const messageOutput = document.querySelector("#message-output");
    const currentRoomLabel = document.querySelector("#current-room-label");
    const participantsList = document.querySelector("#participants-list");

    thisRoom = currentRoomLabel.dataset.roomId;

    // Enter pressed or the send button was pressed    
    sendButton.addEventListener("click", function (event) {
        event.preventDefault();
        
        let messageText = messageInput.value;
        // send message to the server
        sendMessage(messageText);
        messageInput.value = "";

        return false;
    });

    socket = io();
    socket.on('connect', function() {
        //socket.emit('client_connected', {data: 'I\'m connected!'});
        messageInput.disabled = false;
        sendButton.disabled = false;

        join_room(thisRoom);

        if (thisHeartbeatInterval) {
            clearInterval(thisHeartbeatInterval);
        }

        thisHeartbeatInterval = setInterval(() => {
            sendRoomHeartbeat(thisRoom);
        }, 2000);
    });


    socket.on("server_message", function(data) {
        addMessage(messageOutput, data);
    });

    socket.on("server_room", function(data) {
        data.username = "SERVER"
        addMessage(messageOutput, data);
    });

    socket.on("server_participants", function(data) {
        data.username = "SERVER"

        let participantsHtml = "";

        for (participant of data.participants) {
            console.log(participant);
            let active_sec_ago = Math.abs(Math.floor(Date.now()/1000 - parseInt(participant.active_time)));
                if (active_sec_ago < 5) {
                    console.log("participant.active_time " + participant.active_time)
                    console.log("Date.now() " + Date.now())
                    participantsHtml += `<li class="list-group-item">${participant.username} </li>`;
            }
        }

        participantsList.innerHTML = participantsHtml;
    });

});


// Send the server a heartbeat message to let them know this user is still active in the room
function sendRoomHeartbeat() {
    socket.emit('client_heartbeat', {room: thisRoom});
}


// Send a message from client to server
function sendMessage(messageText) {
    socket.emit('client_message', {message: messageText, room: thisRoom});
}

function addMessage(target, data) {
    // data has message, username, room
    usernameBadgeClass = "badge bg-primary";
    messageBadgeClass = "badge rounded-pill bg-light text-dark";
    target.innerHTML += "<div class='msg-row row'>";
    target.innerHTML += `<li><span class="${usernameBadgeClass}"><span class="msg-user">${data.username}:</span> ${data.message}</span></li>`;
    target.innerHTML += "</div>";
}

function join_room(room, username) {
    socket.emit("join", {room: room, username: username})
}