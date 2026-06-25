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
        statusText.textContent = 'Connected';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleAgentEvent(data);
    };

    socket.onclose = () => {
        connectionStatus.className = 'status-dot offline';
        statusText.textContent = 'Disconnected. Retrying...';
        setTimeout(connect, 3000);
    };

    socket.onerror = (err) => {
        console.error('Socket error:', err);
        socket.close();
    };
}

function handleAgentEvent(msg) {
    switch (msg.type) {
        case 'tool_start':
            createMessageElement('system', `🔧 Using ${msg.tool_name}...`);
            break;

        case 'reasoning':
            thinkingIndicator.classList.add('hidden');
            if (!currentAgentMessage || !currentAgentMessage.classList.contains('reasoning')) {
                currentAgentMessage = createMessageElement('agent');
                currentAgentMessage.classList.add('reasoning');
            }
            currentAgentMessage.insertAdjacentText('beforeend', msg.text);
            break;

        case 'text':
            thinkingIndicator.classList.add('hidden');
            if (!currentAgentMessage || currentAgentMessage.classList.contains('reasoning')) {
                currentAgentMessage = createMessageElement('agent');
                currentAgentMessage.classList.add('streaming');
            }
            currentAgentMessage.insertAdjacentText('beforeend', msg.text);
            break;

        case 'done':
            thinkingIndicator.classList.add('hidden');
            if (currentAgentMessage) {
                currentAgentMessage.classList.remove('streaming');
            }
            currentAgentMessage = null;
            if (msg.metadata) {
                const meta = msg.metadata;
                const metaText = [
                    `Status: ${meta.status}`,
                    `Execution time: ${meta.execution_time}s`,
                ].join('  •  ');
                createMessageElement('system', `📊 ${metaText}`);
            }
            break;

        case 'summarized':
            thinkingIndicator.classList.add('hidden');
            currentAgentMessage = null;
            messagesContainer.innerHTML = '';
            loadHistory();
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
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function loadHistory() {
    try {
        const resp = await fetch('http://localhost:8000/history?session_id=default');
        if (!resp.ok) return;
        const messages = await resp.json();
        for (const msg of messages) {
            const role = msg.role;
            const content = msg.content || '';
            const agentName = msg.agent_name;
            if (role === 'user') {
                createMessageElement('user', content);
            } else if (role === 'assistant') {
                createMessageElement('agent', content);
            } else if (role === 'system' && agentName === 'summary') {
                createMessageElement('system', `📝 ${content}`);
            } else if (role === 'system') {
                createMessageElement('system', content);
            }
        }
    } catch (err) {
        console.error('Failed to load history:', err);
    }
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
loadHistory();
