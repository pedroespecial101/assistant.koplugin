// Global state
let eventSource = null;
let allEvents = [];
let stats = {
    total: 0,
    query_start: 0,
    stream_chunk: 0,
    query_complete: 0,
    error: 0,
    heartbeat: 0
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    connectToStream();
    setInterval(updateStats, 2000);
});

// Connect to Server-Sent Events stream
function connectToStream() {
    const statusEl = document.getElementById('connection-status');
    statusEl.textContent = '⚪ Connecting...';
    statusEl.className = 'status-disconnected';
    
    eventSource = new EventSource('/stream');
    
    eventSource.onopen = () => {
        console.log('Connected to event stream');
        statusEl.textContent = '🟢 Connected';
        statusEl.className = 'status-connected';
    };
    
    eventSource.onmessage = (e) => {
        try {
            const event = JSON.parse(e.data);
            handleEvent(event);
        } catch (err) {
            console.error('Error parsing event:', err);
        }
    };
    
    eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
        statusEl.textContent = '🔴 Disconnected';
        statusEl.className = 'status-disconnected';
        
        // Try to reconnect after 3 seconds
        setTimeout(() => {
            eventSource.close();
            connectToStream();
        }, 3000);
    };
}

// Handle incoming event
function handleEvent(event) {
    allEvents.push(event);
    
    // Update stats
    stats.total++;
    const eventType = event.event || 'unknown';
    if (stats[eventType] !== undefined) {
        stats[eventType]++;
    }
    
    // Update event count display
    document.getElementById('event-count').textContent = `${stats.total} events`;
    
    // Route to appropriate handler
    switch (eventType) {
        case 'query_start':
            handleQueryStart(event);
            break;
        case 'stream_chunk':
            handleStreamChunk(event);
            break;
        case 'query_complete':
            handleQueryComplete(event);
            break;
        case 'error':
            handleError(event);
            break;
        case 'heartbeat':
            // Silent, just for connection check
            break;
        default:
            console.log('Unknown event type:', eventType);
    }
    
    // Always update raw events tab
    updateRawEvents(event);
}

// Handle query start event
function handleQueryStart(event) {
    const output = document.getElementById('output');
    const data = event.data || {};
    
    const header = document.createElement('div');
    header.className = 'query-header';
    header.innerHTML = `
        <strong>📤 NEW QUERY</strong><br>
        Provider: ${data.provider || 'unknown'}<br>
        Model: ${data.model || 'unknown'}<br>
        Title: ${data.title || 'untitled'}<br>
        Time: ${formatTime(event.timestamp)}
    `;
    output.appendChild(header);
    
    // Add to prompts tab
    updatePrompts(event);
    
    // Auto-scroll
    output.scrollTop = output.scrollHeight;
}

// Handle streaming chunk
function handleStreamChunk(event) {
    const output = document.getElementById('output');
    const data = event.data || {};
    
    if (data.reasoning) {
        const reasoning = document.createElement('span');
        reasoning.className = 'reasoning';
        reasoning.textContent = `[Thinking: ${data.reasoning}]\n`;
        output.appendChild(reasoning);
    }
    
    if (data.content) {
        const chunk = document.createElement('span');
        chunk.className = 'chunk';
        chunk.textContent = data.content;
        output.appendChild(chunk);
    }
    
    // Auto-scroll
    output.scrollTop = output.scrollHeight;
}

// Handle query complete
function handleQueryComplete(event) {
    const output = document.getElementById('output');
    const data = event.data || {};
    
    const complete = document.createElement('div');
    complete.className = 'query-header';
    complete.style.background = 'rgba(206, 145, 120, 0.1)';
    complete.style.borderLeftColor = '#ce9178';
    
    let info = '<strong>✅ QUERY COMPLETE</strong><br>';
    if (data.tokens) {
        info += `Tokens: ${data.tokens.prompt || 0} prompt + ${data.tokens.completion || 0} completion<br>`;
    }
    if (data.duration) {
        info += `Duration: ${data.duration}ms<br>`;
    }
    info += `Time: ${formatTime(event.timestamp)}`;
    
    complete.innerHTML = info;
    output.appendChild(complete);
    
    // Auto-scroll
    output.scrollTop = output.scrollHeight;
}

// Handle error event
function handleError(event) {
    const output = document.getElementById('output');
    const data = event.data || {};
    
    const error = document.createElement('div');
    error.className = 'error-message';
    error.innerHTML = `
        <strong>❌ ERROR</strong><br>
        ${data.message || 'Unknown error'}<br>
        Time: ${formatTime(event.timestamp)}
    `;
    output.appendChild(error);
    
    // Auto-scroll
    output.scrollTop = output.scrollHeight;
}

// Update prompts display
function updatePrompts(event) {
    const prompts = document.getElementById('prompts');
    const data = event.data || {};
    
    const card = document.createElement('div');
    card.className = 'prompt-card';
    
    const meta = document.createElement('div');
    meta.className = 'prompt-meta';
    meta.innerHTML = `
        <span class="provider">${data.provider || 'unknown'} / ${data.model || 'unknown'}</span>
        <span class="time">${formatTime(event.timestamp)}</span>
    `;
    card.appendChild(meta);
    
    if (data.history && Array.isArray(data.history)) {
        const history = document.createElement('div');
        history.className = 'message-history';
        
        data.history.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${msg.role || 'user'}`;
            msgDiv.innerHTML = `
                <div class="message-role">${msg.role || 'user'}</div>
                <div class="message-content">${escapeHtml(msg.content || '')}</div>
            `;
            history.appendChild(msgDiv);
        });
        
        card.appendChild(history);
    }
    
    prompts.insertBefore(card, prompts.firstChild);
}

// Update raw events display
function updateRawEvents(event) {
    const raw = document.getElementById('raw');
    
    const eventDiv = document.createElement('div');
    eventDiv.className = 'raw-event';
    
    const header = document.createElement('div');
    header.className = 'raw-event-header';
    header.innerHTML = `
        <span class="event-type ${event.event || 'unknown'}">${event.event || 'unknown'}</span>
        <span class="event-time">${formatTime(event.timestamp)}</span>
    `;
    eventDiv.appendChild(header);
    
    const body = document.createElement('pre');
    body.className = 'raw-event-body';
    body.textContent = JSON.stringify(event, null, 2);
    eventDiv.appendChild(body);
    
    raw.insertBefore(eventDiv, raw.firstChild);
    
    // Keep only last 100 events in DOM
    while (raw.children.length > 100) {
        raw.removeChild(raw.lastChild);
    }
}

// Update statistics
function updateStats() {
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-queries').textContent = stats.query_start;
    document.getElementById('stat-chunks').textContent = stats.stream_chunk;
    document.getElementById('stat-errors').textContent = stats.error;
    
    // Update detailed stats
    const details = document.getElementById('stats-details');
    if (details && allEvents.length > 0) {
        const providers = {};
        const models = {};
        
        allEvents.forEach(event => {
            if (event.event === 'query_start' && event.data) {
                const provider = event.data.provider || 'unknown';
                const model = event.data.model || 'unknown';
                providers[provider] = (providers[provider] || 0) + 1;
                models[model] = (models[model] || 0) + 1;
            }
        });
        
        let html = '<h3 style="margin-bottom: 1rem; color: #4ec9b0;">Breakdown</h3>';
        
        if (Object.keys(providers).length > 0) {
            html += '<h4 style="color: #999; margin-top: 1rem;">Providers</h4><ul style="list-style: none; padding-left: 1rem;">';
            Object.entries(providers).forEach(([provider, count]) => {
                html += `<li style="margin: 0.5rem 0;"><strong>${provider}</strong>: ${count} queries</li>`;
            });
            html += '</ul>';
        }
        
        if (Object.keys(models).length > 0) {
            html += '<h4 style="color: #999; margin-top: 1rem;">Models</h4><ul style="list-style: none; padding-left: 1rem;">';
            Object.entries(models).forEach(([model, count]) => {
                html += `<li style="margin: 0.5rem 0;"><strong>${model}</strong>: ${count} queries</li>`;
            });
            html += '</ul>';
        }
        
        details.innerHTML = html;
    }
}

// Tab switching
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tabs .tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Show empty state if needed
    checkEmptyState(tabName);
}

// Check and show empty state
function checkEmptyState(tabName) {
    const containers = {
        'output': document.getElementById('output'),
        'prompts': document.getElementById('prompts'),
        'raw': document.getElementById('raw')
    };
    
    const container = containers[tabName];
    if (!container) return;
    
    if (container.children.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No events yet</div>
                <div class="empty-state-hint">Waiting for data from your Kindle...</div>
            </div>
        `;
    }
}

// Clear all events
function clearEvents() {
    if (!confirm('Clear all events?')) return;
    
    fetch('/api/clear', { method: 'POST' })
        .then(res => res.json())
        .then(() => {
            allEvents = [];
            stats = {
                total: 0,
                query_start: 0,
                stream_chunk: 0,
                query_complete: 0,
                error: 0,
                heartbeat: 0
            };
            
            document.getElementById('output').innerHTML = '';
            document.getElementById('prompts').innerHTML = '';
            document.getElementById('raw').innerHTML = '';
            
            updateStats();
            
            // Show empty states
            ['output', 'prompts', 'raw'].forEach(checkEmptyState);
        })
        .catch(err => console.error('Error clearing events:', err));
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize empty states
window.addEventListener('load', () => {
    ['output', 'prompts', 'raw'].forEach(checkEmptyState);
});
