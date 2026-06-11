const chatContainer = document.getElementById('chat-container');
const messagesContainer = document.getElementById('messages');
const thinkingIndicator = document.getElementById('thinking-indicator');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');

let socket;
let currentAgentMessage = null;

function connect() {
    socket = new WebSocket('ws://localhost:8000/ws');

    socket.onopen = () => {
        connectionStatus.className = 'status-dot online';
        statusText.innerText = 'Connected';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleAgentEvent(data);
    };

    socket.onclose = () => {
        connectionStatus.className = 'status-dot offline';
        statusText.innerText = 'Disconnected. Retrying...';
        setTimeout(connect, 3000);
    };

    socket.onerror = (err) => {
        console.error('Socket error:', err);
        socket.close();
    };
}

function handleAgentEvent(msg) {
    switch (msg.type) {
        case 'node_start':
            createMessageElement('system', `🔄 ${msg.node_id} taking control`);
            thinkingIndicator.classList.remove('hidden');
            break;

        case 'reasoning':
            thinkingIndicator.classList.add('hidden');
            if (!currentAgentMessage || !currentAgentMessage.classList.contains('reasoning')) {
                currentAgentMessage = createMessageElement('agent');
                currentAgentMessage.classList.add('reasoning');
            }
            currentAgentMessage.innerText += msg.text;
            break;

        case 'text':
            thinkingIndicator.classList.add('hidden');
            if (!currentAgentMessage || currentAgentMessage.classList.contains('reasoning')) {
                currentAgentMessage = createMessageElement('agent');
                currentAgentMessage.classList.add('streaming');
            }
            currentAgentMessage.innerText += msg.text;
            break;

        case 'handoff':
            thinkingIndicator.classList.add('hidden');
            createMessageElement('system', `🔀 Handoff: ${msg.from} → ${msg.to}`);
            currentAgentMessage = null;
            break;

        case 'done':
            thinkingIndicator.classList.add('hidden');
            currentAgentMessage = null;
            if (msg.text) {
                createMessageElement('agent', msg.text);
            }
            if (msg.metadata) {
                const meta = msg.metadata;
                const metaText = [
                    `Status: ${meta.status}`,
                    `Execution time: ${meta.execution_time}s`,
                    `Execution count: ${meta.execution_count}`,
                    `Tokens: ${meta.input_token} in / ${meta.output_token} out`,
                ].join('  •  ');
                createMessageElement('system', `📊 ${metaText}`);
            }
            break;

        default:
            if (msg.error) {
                thinkingIndicator.classList.add('hidden');
                createMessageElement('agent', `Error: ${msg.error}`);
                currentAgentMessage = null;
            }
            break;
    }

    scrollToBottom();
}

function createMessageElement(role, text = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.innerText = text;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    currentAgentMessage = null;
    createMessageElement('user', query);

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(query);
        thinkingIndicator.classList.remove('hidden');
    }

    userInput.value = '';
    scrollToBottom();
});

connect();
