const chatContainer = document.getElementById('chat-container');
const messagesContainer = document.getElementById('messages');
const thinkingIndicator = document.getElementById('thinking-indicator');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');

function getSessionId() {
    return new URLSearchParams(window.location.search).get('session_id') || 'default';
}

const SESSION_ID = getSessionId();

let socket;
let currentAgentMessage = null;
let currentAgentText = '';
let currentReasoningText = '';

function connect() {
    const wsUrl = 'ws://' + window.location.hostname + ':8000/ws?session_id=' + SESSION_ID;
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
        setTimeout(connect, 3000);
    };

    socket.onerror = (err) => {
        console.error('Socket error:', err);
        socket.close();
    };
}

function renderMarkdown(text) {
    if (!text) return '';

    // 0. convert literal HTML tags to markdown (agent sometimes outputs HTML)
    text = text
        .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
        .replace(/<em>(.*?)<\/em>/g, '*$1*')
        .replace(/<b>(.*?)<\/b>/g, '**$1**')
        .replace(/<i>(.*?)<\/i>/g, '*$1*')
        .replace(/<code>(.*?)<\/code>/g, '`$1`')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<p>/gi, '')
        .replace(/<\/p>/gi, '\n\n');

    // 1. protect fenced code blocks (before HTML escape)
    var blocks = [];
    text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
        blocks.push('<pre><code>' + code + '</code></pre>');
        return '%%B' + (blocks.length - 1) + '%%';
    });

    // 2. protect blockquotes (strip > prefix, escape first, then inline formatting)
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

    // 3. HTML-escape everything that remains
    var html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // 4. block-level elements
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/^---\s*$/gm, '<hr>');

    // 5. inline formatting (order matters)
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

    // 6. lists
    html = html.replace(/^- \[x\] (.+)$/gm, '<li><input type="checkbox" checked disabled> $1</li>');
    html = html.replace(/^- \[ \] (.+)$/gm, '<li><input type="checkbox" disabled> $1</li>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>');

    // 7. tables
    html = html.replace(/^\|(.+)\|$/gm, function (row) {
        var inner = row.replace(/^\|/, '').replace(/\|$/, '');
        if (/^[\s\-:|]+$/.test(inner)) return '';
        var cells = inner.split('|');
        for (var i = 0; i < cells.length; i++) cells[i] = '<td>' + cells[i].trim() + '</td>';
        return '<tr>' + cells.join('') + '</tr>';
    });
    html = html.replace(/(<tr>.*?<\/tr>(?:\n?<tr>.*?<\/tr>)*)/g, '<table>$1</table>');

    // 8. paragraphs & line breaks (no lookbehinds)
    html = html.replace(/\n\n+/g, '%%P%%');
    html = html.replace(/\n/g, '<br>');
    html = html.replace(/%%P%%/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // 9. inline code (after paragraph wrapping so it stays inline)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 10. restore protected blocks — unwrap from <p>
    for (var i = 0; i < blocks.length; i++) {
        html = html.replace(new RegExp('<p>%%B' + i + '%%</p>|%%B' + i + '%%', 'g'), blocks[i]);
    }

    // 11. remove empty paragraphs
    html = html.replace(/<p>\s*(?:<br>\s*)?<\/p>/g, '');

    return html;
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

        case 'done':
            thinkingIndicator.classList.add('hidden');
            if (currentAgentMessage) {
                currentAgentMessage.classList.remove('streaming');
            }
            currentAgentMessage = null;
            currentAgentText = '';
            currentReasoningText = '';
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
            currentAgentText = '';
            currentReasoningText = '';
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
    if (role === 'agent' || role === 'system') {
        messageDiv.innerHTML = renderMarkdown(text);
    } else {
        messageDiv.textContent = text;
    }
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function loadHistory() {
    try {
        const resp = await fetch('http://localhost:8000/history?session_id=' + SESSION_ID);
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
    currentAgentText = '';
    currentReasoningText = '';
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
