const chatContainer = document.getElementById('chat-container');
const messagesContainer = document.getElementById('messages');
const thinkingIndicator = document.getElementById('thinking-indicator');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');
const sessionListEl = document.getElementById('session-list');
const newChatBtn = document.getElementById('new-chat-btn');

function getSessionId() {
    return new URLSearchParams(window.location.search).get('session_id') || 'default';
}

let activeSessionId = getSessionId();
let socket;
let sessions = [];
let currentAgentMessage = null;
let currentAgentText = '';
let currentReasoningText = '';
let autoReconnect = true;
let pendingConfirmation = false;
let isStreaming = false;

function connect(sessionId) {
    autoReconnect = true;
    if (socket) {
        socket.onclose = null;
        socket.onerror = null;
        socket.close();
    }
    const wsUrl = 'ws://' + window.location.hostname + ':8000/ws?session_id=' + sessionId;
    socket = new WebSocket(wsUrl);

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
        if (autoReconnect) {
            setTimeout(() => connect(activeSessionId), 3000);
        }
    };

    socket.onerror = (err) => {
        console.error('Socket error:', err);
        socket.close();
    };
}

async function loadSessions() {
    try {
        const resp = await fetch('http://localhost:8000/sessions');
        if (!resp.ok) return;
        sessions = await resp.json();
        renderSessionList();
    } catch (err) {
        console.error('Failed to load sessions:', err);
    }
}

function renderSessionList() {
    sessionListEl.innerHTML = '';
    for (const s of sessions) {
        const el = document.createElement('div');
        el.className = 'session-item' + (s.id === activeSessionId ? ' active' : '');

        const titleSpan = document.createElement('span');
        titleSpan.className = 'session-title';
        titleSpan.textContent = s.title || 'New chat';
        titleSpan.addEventListener('click', () => switchToSession(s.id));

        const delBtn = document.createElement('button');
        delBtn.className = 'session-delete';
        delBtn.textContent = '\u00D7';
        delBtn.title = 'Delete session';
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(s.id);
        });

        el.appendChild(titleSpan);
        el.appendChild(delBtn);
        sessionListEl.appendChild(el);
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Delete this session?')) return;
    try {
        const resp = await fetch('http://localhost:8000/sessions/' + sessionId, {method: 'DELETE'});
        if (!resp.ok) return;
        sessions = sessions.filter(s => s.id !== sessionId);
        if (sessionId === activeSessionId) {
            const next = sessions[0] || {id: 'default', title: 'New chat'};
            await switchToSession(next.id);
        } else {
            renderSessionList();
        }
    } catch (err) {
        console.error('Failed to delete session:', err);
    }
}

async function switchToSession(sessionId) {
    if (sessionId === activeSessionId) return;
    activeSessionId = sessionId;
    messagesContainer.innerHTML = '';
    currentAgentMessage = null;
    currentAgentText = '';
    currentReasoningText = '';
    thinkingIndicator.classList.add('hidden');
    connect(sessionId);
    await loadHistory(sessionId);
    renderSessionList();
    const url = new URL(window.location);
    url.searchParams.set('session_id', sessionId);
    window.history.replaceState({}, '', url);
}

function createNewSession() {
    const newId = crypto.randomUUID();
    const now = new Date().toISOString();
    sessions.unshift({id: newId, title: 'New chat', last_updated: now});
    renderSessionList();
    switchToSession(newId);
}

async function loadHistory(sessionId) {
    try {
        const resp = await fetch('http://localhost:8000/history?session_id=' + sessionId);
        if (!resp.ok) return;
        const messages = await resp.json();
        for (const msg of messages) {
            const role = msg.role;
            const content = msg.content || '';
            if (role === 'user') {
                createMessageElement('user', content);
            } else if (role === 'assistant') {
                createMessageElement('agent', content);
            } else if (role === 'system') {
                createMessageElement('system', content);
            }
        }
    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

function renderMarkdown(text) {
    if (!text) return '';

    text = text
        .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
        .replace(/<em>(.*?)<\/em>/g, '*$1*')
        .replace(/<b>(.*?)<\/b>/g, '**$1**')
        .replace(/<i>(.*?)<\/i>/g, '*$1*')
        .replace(/<code>(.*?)<\/code>/g, '`$1`')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<p>/gi, '')
        .replace(/<\/p>/gi, '\n\n');

    var blocks = [];
    text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
        blocks.push('<pre><code>' + code + '</code></pre>');
        return '%%B' + (blocks.length - 1) + '%%';
    });

    text = text.replace(/^> (.+)$/gm, function (_, content) {
        var inner = content
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        inner = inner
            .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/~~(.+?)~~/g, '<del>$1</del>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
            .replace(/`([^`]+)`/g, '<code>$1</code>');
        blocks.push('<blockquote>' + inner + '</blockquote>');
        return '%%B' + (blocks.length - 1) + '%%';
    });

    var html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/^---\s*$/gm, '<hr>');

    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

    html = html.replace(/^- \[x\] (.+)$/gm, '<li><input type="checkbox" checked disabled> $1</li>');
    html = html.replace(/^- \[ \] (.+)$/gm, '<li><input type="checkbox" disabled> $1</li>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>');

    html = html.replace(/^\|(.+)\|$/gm, function (row) {
        var inner = row.replace(/^\|/, '').replace(/\|$/, '');
        if (/^[\s\-:|]+$/.test(inner)) return '';
        var cells = inner.split('|');
        for (var i = 0; i < cells.length; i++) cells[i] = '<td>' + cells[i].trim() + '</td>';
        return '<tr>' + cells.join('') + '</tr>';
    });
    html = html.replace(/(<tr>.*?<\/tr>(?:\n?<tr>.*?<\/tr>)*)/g, '<table>$1</table>');

    html = html.replace(/\n\n+/g, '%%P%%');
    html = html.replace(/\n/g, '<br>');
    html = html.replace(/%%P%%/g, '</p><p>');
    html = '<p>' + html + '</p>';

    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    for (var i = 0; i < blocks.length; i++) {
        html = html.replace(new RegExp('<p>%%B' + i + '%%</p>|%%B' + i + '%%', 'g'), blocks[i]);
    }

    html = html.replace(/<p>\s*(?:<br>\s*)?<\/p>/g, '');

    return html;
}

function handleAgentEvent(msg) {
    switch (msg.type) {
        case 'tool_start':
            createMessageElement('system', '\uD83D\uDD27 Using ' + msg.tool_name + '...');
            break;

        case 'reasoning':
            thinkingIndicator.classList.add('hidden');
            if (!currentAgentMessage || !currentAgentMessage.classList.contains('reasoning')) {
                currentAgentMessage = createMessageElement('agent');
                currentAgentMessage.classList.add('reasoning');
                currentReasoningText = '';
            }
            currentReasoningText += msg.text;
            currentAgentMessage.innerHTML = renderMarkdown(currentReasoningText);
            break;

        case 'text':
            thinkingIndicator.classList.add('hidden');
            if (!currentAgentMessage || currentAgentMessage.classList.contains('reasoning')) {
                currentAgentMessage = createMessageElement('agent');
                currentAgentMessage.classList.add('streaming');
                currentAgentText = '';
            }
            currentAgentText += msg.text;
            currentAgentMessage.innerHTML = renderMarkdown(currentAgentText);
            break;

        case 'confirmation_required':
            showConfirmation(msg.prompt);
            break;

        case 'done':
            thinkingIndicator.classList.add('hidden');
            document.getElementById('stop-btn').classList.add('hidden');
            isStreaming = false;
            enableInput();
            if (currentAgentMessage) {
                currentAgentMessage.classList.remove('streaming');
            }
            if (currentAgentText) {
                updateSessionTitle(activeSessionId, currentAgentText);
            }
            currentAgentMessage = null;
            currentAgentText = '';
            currentReasoningText = '';
            if (msg.metadata) {
                const meta = msg.metadata;
                let metaText;
                if (meta.status === 'CANCELLED') {
                    metaText = '\u26A0\uFE0F Stopped by user';
                } else {
                    metaText = 'Status: ' + meta.status + '  \u2022  Execution time: ' + meta.execution_time + 's';
                }
                createMessageElement('system', '\uD83D\uDCCA ' + metaText);
            }
            break;

        case 'summarized':
            thinkingIndicator.classList.add('hidden');
            document.getElementById('stop-btn').classList.add('hidden');
            isStreaming = false;
            currentAgentMessage = null;
            currentAgentText = '';
            currentReasoningText = '';
            messagesContainer.innerHTML = '';
            loadHistory(activeSessionId);
            break;

        default:
            if (msg.error) {
                thinkingIndicator.classList.add('hidden');
                document.getElementById('stop-btn').classList.add('hidden');
                isStreaming = false;
                enableInput();
                createMessageElement('agent', 'Error: ' + msg.error);
                currentAgentMessage = null;
            }
            break;
    }

    scrollToBottom();
}

function updateSessionTitle(sessionId, text) {
    const session = sessions.find(s => s.id === sessionId);
    if (session && session.title === 'New chat') {
        session.title = text.trim().slice(0, 80);
        renderSessionList();
    }
}

function createMessageElement(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + role + '-message';
    if (role === 'agent' || role === 'system') {
        messageDiv.innerHTML = renderMarkdown(text || '');
    } else {
        messageDiv.textContent = text || '';
    }
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

document.getElementById('stop-btn').addEventListener('click', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({type: "stop"}));
    }
});

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query || isStreaming) return;

    currentAgentMessage = null;
    currentAgentText = '';
    currentReasoningText = '';
    createMessageElement('user', query);

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({text: query}));
        isStreaming = true;
        document.getElementById('stop-btn').classList.remove('hidden');
        thinkingIndicator.classList.remove('hidden');
    }

    userInput.value = '';
    scrollToBottom();
});

function showConfirmation(prompt) {
    pendingConfirmation = true;
    userInput.disabled = true;
    document.getElementById('send-btn').disabled = true;
    const banner = document.getElementById('confirmation-banner');
    banner.querySelector('.confirmation-prompt').textContent = prompt;
    banner.classList.remove('hidden');
    scrollToBottom();
}

function handleConfirm(approved) {
    pendingConfirmation = false;
    document.getElementById('confirmation-banner').classList.add('hidden');
    socket.send(JSON.stringify({type: "confirm", response: approved ? "yes" : "no"}));
}

function enableInput() {
    userInput.disabled = false;
    document.getElementById('send-btn').disabled = false;
    pendingConfirmation = false;
}

newChatBtn.addEventListener('click', createNewSession);

async function init() {
    connect(activeSessionId);
    await loadSessions();
    await loadHistory(activeSessionId);
}

init();
