/**
 * C/C++ Concept Search - Web Application
 * Frontend for semantic search with AI chat
 */

// ==================== State ====================

const state = {
    currentSearch: null,
    currentResults: [],
    originalResults: [],
    displayResults: [],
    currentConceptId: null,
    currentBookFilter: null,
    chatHistory: []
};

// ==================== DOM Elements ====================

const elements = {
    // Search
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    searchBtnText: document.getElementById('searchBtnText'),
    searchSpinner: document.getElementById('searchSpinner'),

    // Results
    resultsSection: document.getElementById('resultsSection'),
    bookLegend: document.getElementById('bookLegend'),
    summaryTable: document.getElementById('summaryTable'),
    resultsList: document.getElementById('resultsList'),
    loadMoreContainer: document.getElementById('loadMoreContainer'),
    loadMoreBtn: document.getElementById('loadMoreBtn'),
    filterBtn: document.getElementById('filterBtn'),
    newSearchBtn: document.getElementById('newSearchBtn'),

    // Empty states
    emptyState: document.getElementById('emptyState'),
    noResults: document.getElementById('noResults'),

    // Concept modal
    conceptModal: document.getElementById('conceptModal'),
    conceptDetail: document.getElementById('conceptDetail'),
    closeConceptBtn: document.getElementById('closeConceptBtn'),
    chatBtn: document.getElementById('chatBtn'),
    codeBtn: document.getElementById('codeBtn'),
    backBtn: document.getElementById('backBtn'),
    conceptOverlay: document.getElementById('conceptOverlay'),

    // Chat modal
    chatModal: document.getElementById('chatModal'),
    chatTitle: document.getElementById('chatTitle'),
    chatHistory: document.getElementById('chatHistory'),
    chatInput: document.getElementById('chatInput'),
    sendChatBtn: document.getElementById('sendChatBtn'),
    closeChatBtn: document.getElementById('closeChatBtn'),
    chatOverlay: document.getElementById('chatOverlay'),

    // Filter modal
    filterModal: document.getElementById('filterModal'),
    filterOptions: document.getElementById('filterOptions'),
    cancelFilterBtn: document.getElementById('cancelFilterBtn'),
    closeFilterBtn: document.getElementById('closeFilterBtn'),
    filterOverlay: document.getElementById('filterOverlay'),

    // Notifications
    errorNotification: document.getElementById('errorNotification'),
    errorText: document.getElementById('errorText'),
    successNotification: document.getElementById('successNotification'),
    successText: document.getElementById('successText'),
};

// ==================== Event Listeners ====================

// Search
elements.searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

elements.searchBtn.addEventListener('click', performSearch);

// Modals
elements.closeConceptBtn.addEventListener('click', closeConceptModal);
elements.conceptOverlay.addEventListener('click', closeConceptModal);
elements.backBtn.addEventListener('click', closeConceptModal);

elements.closeChatBtn.addEventListener('click', closeChatModal);
elements.chatOverlay.addEventListener('click', closeChatModal);
elements.sendChatBtn.addEventListener('click', sendChatMessage);
elements.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        sendChatMessage();
    }
});

elements.closeFilterBtn.addEventListener('click', closeFilterModal);
elements.filterOverlay.addEventListener('click', closeFilterModal);
elements.cancelFilterBtn.addEventListener('click', closeFilterModal);

// Filter and navigation
elements.filterBtn.addEventListener('click', openFilterModal);
elements.newSearchBtn.addEventListener('click', () => {
    elements.resultsSection.style.display = 'none';
    elements.searchInput.focus();
});

elements.loadMoreBtn.addEventListener('click', showAllResults);

// Notification close buttons
document.querySelectorAll('.notification-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.target.closest('.notification').style.display = 'none';
    });
});

// ==================== Search & Results ====================

async function performSearch() {
    const query = elements.searchInput.value.trim();

    if (!query) {
        showError('Please enter a search query');
        return;
    }

    setLoading(true);

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        state.currentSearch = query;
        state.originalResults = data.results || [];
        state.currentResults = state.originalResults;
        state.currentBookFilter = null;
        state.displayResults = state.currentResults.slice(0, 10);

        if (state.currentResults.length === 0) {
            elements.resultsSection.style.display = 'none';
            elements.noResults.style.display = 'block';
            return;
        }

        elements.noResults.style.display = 'none';
        displayResults(data.summary || []);

    } catch (error) {
        showError(`Search error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

function displayResults(summary) {
    // Show results section
    elements.resultsSection.style.display = 'block';

    // Render book legend
    renderBookLegend(summary);

    // Render summary table
    renderSummaryTable(summary);

    // Render results list
    renderResultsList(state.displayResults);

    // Show/hide load more button
    if (state.currentResults.length > 10) {
        elements.loadMoreContainer.style.display = 'flex';
    } else {
        elements.loadMoreContainer.style.display = 'none';
    }

    // Update load more button text
    if (state.displayResults.length < state.currentResults.length) {
        elements.loadMoreBtn.textContent = `Show All ${state.currentResults.length} Results`;
    }
}

function renderBookLegend(summary) {
    let html = '<div class="book-legend-title">Book Sources:</div>';

    summary.forEach(book => {
        html += `
            <div class="book-legend-item">
                <div class="book-color-dot" style="background-color: ${getBookColor(book.color)};"></div>
                <div class="book-legend-text">
                    ${book.display}
                    <span class="book-legend-count" style="color: #BCBCBC;"> (${book.count})</span>
                </div>
            </div>
        `;
    });

    elements.bookLegend.innerHTML = html;
}

function renderSummaryTable(summary) {
    let html = `
        <div class="summary-table-title">Search Results Summary</div>
        <div class="summary-table-content">
            <div class="summary-table-row">
                <div class="summary-table-header">Book</div>
                <div class="summary-table-header">Matches</div>
                <div class="summary-table-header">Top Score</div>
            </div>
    `;

    summary.forEach(book => {
        html += `
            <div class="summary-table-row">
                <div class="summary-table-cell">
                    <span style="color: ${getBookColor(book.color)};">■</span>
                    ${book.display}
                </div>
                <div class="summary-table-cell">${book.count}</div>
                <div class="summary-table-cell">${book.top_score}%</div>
            </div>
        `;
    });

    html += '</div>';
    elements.summaryTable.innerHTML = html;
}

function renderResultsList(results) {
    elements.resultsList.innerHTML = results.map(result => `
        <div class="result-item" onclick="viewConcept('${result.id}')">
            <div class="result-score">[${result.score}%]</div>
            <div class="result-content">
                <div class="result-topic">${escapeHtml(result.topic)}</div>
                <div class="result-book" style="border-color: ${getBookColor(result.book_color)}; color: ${getBookColor(result.book_color)};">
                    ${result.book_display}
                </div>
            </div>
        </div>
    `).join('');
}

function showAllResults() {
    state.displayResults = state.currentResults;
    renderResultsList(state.displayResults);
    elements.loadMoreContainer.style.display = 'none';
}

// ==================== Concept Detail ====================

async function viewConcept(conceptId) {
    state.currentConceptId = conceptId;

    // Find the concept in results to get book info
    const conceptData = state.currentResults.find(c => c.id === conceptId);
    if (!conceptData) {
        showError('Concept not found');
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`/api/concept/${conceptId}`);

        if (!response.ok) {
            throw new Error('Failed to load concept');
        }

        const concept = await response.json();

        // Render concept detail
        renderConceptDetail(concept);

        // Show chat button if API key is available
        elements.chatBtn.style.display = concept.has_explanation ? 'inline-flex' : 'none';

        // Show code button if code exists
        elements.codeBtn.style.display = concept.has_code ? 'inline-flex' : 'none';

        // Open modal
        elements.conceptModal.style.display = 'flex';
        state.chatHistory = []; // Reset chat history

    } catch (error) {
        showError(`Failed to load concept: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

function renderConceptDetail(concept) {
    const color = getBookColor(concept.book_color);

    let html = `
        <h1 class="concept-title">${escapeHtml(concept.topic)}</h1>

        <div class="concept-meta">
            <div class="concept-meta-item">
                <span class="concept-meta-label">Source</span>
                <span class="concept-meta-value" style="color: ${color};">● ${concept.book_display}</span>
            </div>
            <div class="concept-meta-item">
                <span class="concept-meta-label">ID</span>
                <span class="concept-meta-value dim">${concept.id}</span>
            </div>
        </div>

        <div class="concept-explanation">
            ${markdownToHtml(concept.explanation)}
        </div>
    `;

    if (concept.syntax) {
        html += `
            <div class="concept-code">
                <div class="concept-code-label">Syntax Reference:</div>
                <pre>${escapeHtml(concept.syntax)}</pre>
            </div>
        `;
    }

    if (concept.code_example) {
        html += `
            <div class="concept-code">
                <div class="concept-code-label">Code Example:</div>
                <pre>${escapeHtml(concept.code_example)}</pre>
            </div>
        `;
    }

    elements.conceptDetail.innerHTML = html;
}

function closeConceptModal() {
    elements.conceptModal.style.display = 'none';
    state.currentConceptId = null;
}

// ==================== Chat ====================

elements.chatBtn.addEventListener('click', () => {
    if (!state.currentConceptId) return;

    const concept = state.currentResults.find(c => c.id === state.currentConceptId);
    if (!concept) return;

    elements.chatTitle.textContent = `Chat about: ${concept.topic}`;
    elements.chatHistory.innerHTML = '';
    state.chatHistory = [];

    elements.chatModal.style.display = 'flex';
    elements.chatInput.focus();

    closeConceptModal();
});

async function sendChatMessage() {
    const message = elements.chatInput.value.trim();

    if (!message) return;

    if (!state.currentConceptId) {
        showError('No concept selected for chat');
        return;
    }

    // Check for exit command
    if (message.toLowerCase() === 'exit' || message.toLowerCase() === 'quit') {
        closeChatModal();
        return;
    }

    // Add user message to history
    addChatMessage('user', message);
    elements.chatInput.value = '';
    elements.sendChatBtn.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                concept_id: state.currentConceptId,
                message: message,
                history: state.chatHistory
            })
        });

        if (!response.ok) {
            throw new Error(`Chat failed: ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        // Add assistant message
        addChatMessage('assistant', data.response);

        // Update state history
        state.chatHistory.push({ role: 'user', content: message });
        state.chatHistory.push({ role: 'assistant', content: data.response });

        // Scroll to bottom
        elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;

    } catch (error) {
        showError(`Chat error: ${error.message}`);
    } finally {
        elements.sendChatBtn.disabled = false;
        elements.chatInput.focus();
    }
}

function addChatMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    messageDiv.innerHTML = `
        <span class="chat-label">${role === 'user' ? 'You' : 'Assistant'}</span>
        <div class="chat-bubble">${markdownToHtml(text)}</div>
    `;

    elements.chatHistory.appendChild(messageDiv);
}

function closeChatModal() {
    elements.chatModal.style.display = 'none';
    state.chatHistory = [];
}

// ==================== Filter ====================

function openFilterModal() {
    const books = [...new Set(state.originalResults.map(r => r.book))];

    let html = '';

    books.forEach(book => {
        const count = state.originalResults.filter(r => r.book === book).length;
        const bookData = state.originalResults.find(r => r.book === book);
        const color = getBookColor(bookData.book_color);

        html += `
            <label class="filter-option">
                <input type="radio" name="book-filter" value="${book}" ${state.currentBookFilter === book ? 'checked' : ''}>
                <span class="filter-option-label">
                    <span style="color: ${color};">●</span>
                    ${bookData.book_display}
                </span>
                <span class="filter-option-count">${count}</span>
            </label>
        `;
    });

    // Add "show all" option
    html += `
        <label class="filter-option">
            <input type="radio" name="book-filter" value="" ${!state.currentBookFilter ? 'checked' : ''}>
            <span class="filter-option-label">All Books</span>
            <span class="filter-option-count">${state.originalResults.length}</span>
        </label>
    `;

    elements.filterOptions.innerHTML = html;

    // Add change listener
    document.querySelectorAll('input[name="book-filter"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const selectedBook = e.target.value;

            if (selectedBook) {
                state.currentResults = state.originalResults.filter(r => r.book === selectedBook);
                state.currentBookFilter = selectedBook;
            } else {
                state.currentResults = state.originalResults;
                state.currentBookFilter = null;
            }

            state.displayResults = state.currentResults.slice(0, 10);
            renderResultsList(state.displayResults);

            if (state.currentResults.length > 10) {
                elements.loadMoreContainer.style.display = 'flex';
            } else {
                elements.loadMoreContainer.style.display = 'none';
            }

            closeFilterModal();
        });
    });

    elements.filterModal.style.display = 'flex';
}

function closeFilterModal() {
    elements.filterModal.style.display = 'none';
}

// ==================== Utilities ====================

function setLoading(loading) {
    if (loading) {
        elements.searchBtnText.style.display = 'none';
        elements.searchSpinner.style.display = 'inline-block';
        elements.searchBtn.disabled = true;
    } else {
        elements.searchBtnText.style.display = 'inline';
        elements.searchSpinner.style.display = 'none';
        elements.searchBtn.disabled = false;
    }
}

function showError(message) {
    elements.errorText.textContent = message;
    elements.errorNotification.style.display = 'flex';
    setTimeout(() => {
        elements.errorNotification.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    elements.successText.textContent = message;
    elements.successNotification.style.display = 'flex';
    setTimeout(() => {
        elements.successNotification.style.display = 'none';
    }, 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function markdownToHtml(text) {
    if (!text) return '';

    // Basic markdown to HTML conversion
    text = escapeHtml(text);

    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Code blocks
    text = text.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');

    // Inline code
    text = text.replace(/`(.*?)`/g, '<code style="background: rgba(95, 255, 255, 0.1); padding: 2px 4px; border-radius: 2px;">$1</code>');

    // Line breaks
    text = text.replace(/\n/g, '<br>');

    return text;
}

function getBookColor(colorName) {
    const colors = {
        'cyan': '#5FFFFF',
        'green': '#5FFF5F',
        'red': '#FF5F5F',
        'yellow': '#FFFF5F',
        'magenta': '#FF5FFF',
        'bright_blue': '#5F87FF',
        'bright_red': '#FF5F5F',
        'bright_green': '#5FFF5F',
        'bright_yellow': '#FFFF5F',
        'bright_magenta': '#FF5FFF',
        'bright_cyan': '#5FFFFF',
        'blue': '#5F87AF',
        'white': '#FFFFFF',
        'grey70': '#BCBCBC',
        'dim': '#BCBCBC'
    };

    return colors[colorName] || '#FFFFFF';
}

// Initialize on load
window.addEventListener('load', () => {
    elements.searchInput.focus();
    console.log('C/C++ Concept Search ready');
});
