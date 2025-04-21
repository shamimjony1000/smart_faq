// Main JavaScript for Arogga FAQ Assistant

// Global variables
let currentConversationId = null;

// Function to create typewriter effect
function typeWriter(element, text, speed = 20, index = 0) {
    if (index < text.length) {
        element.innerHTML += text.charAt(index);
        index++;
        setTimeout(() => typeWriter(element, text, speed, index), speed);
    }
}

// Theme toggle functionality
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const lightIcon = document.getElementById('lightIcon');
    const darkIcon = document.getElementById('darkIcon');
    
    // Check for saved theme preference or use device preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'inline-block';
    }
    
    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        let newTheme;
        
        if (currentTheme === 'dark') {
            newTheme = 'light';
            lightIcon.style.display = 'inline-block';
            darkIcon.style.display = 'none';
        } else {
            newTheme = 'dark';
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'inline-block';
        }
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

// Load conversations from database
function loadConversations() {
    $.ajax({
        url: '/conversations',
        type: 'GET',
        success: function(conversations) {
            const chatHistory = document.querySelector('.chat-history');
            
            // Clear existing history items
            chatHistory.innerHTML = '';
            
            // Group conversations by date
            const today = new Date().toDateString();
            const yesterday = new Date(Date.now() - 86400000).toDateString();
            
            let todayItems = [];
            let yesterdayItems = [];
            let olderItems = [];
            
            conversations.forEach(conversation => {
                const date = new Date(conversation.created_at).toDateString();
                const item = createHistoryItem(conversation);
                
                if (date === today) {
                    todayItems.push(item);
                } else if (date === yesterday) {
                    yesterdayItems.push(item);
                } else {
                    olderItems.push(item);
                }
            });
            
            // Add today's conversations
            if (todayItems.length > 0) {
                const todayHeading = document.createElement('h6');
                todayHeading.className = 'history-heading';
                todayHeading.textContent = 'Today';
                chatHistory.appendChild(todayHeading);
                
                todayItems.forEach(item => chatHistory.appendChild(item));
            }
            
            // Add yesterday's conversations
            if (yesterdayItems.length > 0) {
                const yesterdayHeading = document.createElement('h6');
                yesterdayHeading.className = 'history-heading';
                yesterdayHeading.textContent = 'Yesterday';
                chatHistory.appendChild(yesterdayHeading);
                
                yesterdayItems.forEach(item => chatHistory.appendChild(item));
            }
            
            // Add older conversations
            if (olderItems.length > 0) {
                const olderHeading = document.createElement('h6');
                olderHeading.className = 'history-heading';
                olderHeading.textContent = 'Previous 7 Days';
                chatHistory.appendChild(olderHeading);
                
                olderItems.forEach(item => chatHistory.appendChild(item));
            }
            
            // If no conversations, add a message
            if (conversations.length === 0) {
                const emptyMessage = document.createElement('div');
                emptyMessage.className = 'empty-history-message';
                emptyMessage.textContent = 'No conversations yet';
                chatHistory.appendChild(emptyMessage);
            }
        },
        error: function(error) {
            console.error('Error loading conversations:', error);
        }
    });
}

// Create a history item element
function createHistoryItem(conversation) {
    const item = document.createElement('div');
    item.className = 'history-item';
    item.dataset.id = conversation.id;
    
    const icon = document.createElement('i');
    icon.className = 'bi bi-chat-left-text';
    
    const span = document.createElement('span');
    span.textContent = conversation.title;
    
    item.appendChild(icon);
    item.appendChild(span);
    
    // Add click event to load conversation
    item.addEventListener('click', function() {
        loadConversation(conversation.id);
        
        // Update active state
        document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            document.querySelector('.sidebar').classList.add('collapsed');
        }
    });
    
    return item;
}

// Load a specific conversation
function loadConversation(conversationId) {
    console.log("Loading conversation:", conversationId);
    $.ajax({
        url: `/conversation/${conversationId}`,
        type: 'GET',
        success: function(conversation) {
            console.log("Loaded conversation:", conversation);
            currentConversationId = conversation.id;
            
            // Clear chat body
            const chatBody = document.getElementById('chatBody');
            chatBody.innerHTML = '';
            
            // Add all messages
            conversation.messages.forEach(message => {
                addMessageToUI(message.content, message.is_user, false);
            });
            
            // If no messages, add welcome message
            if (conversation.messages.length === 0) {
                const welcomeText = "Hello! I'm Arogga FAQ Assistant. How can I help you today?";
                addMessageToUI(welcomeText, false, true);
            }
            
            // Scroll to bottom
            chatBody.scrollTop = chatBody.scrollHeight;
        },
        error: function(error) {
            console.error('Error loading conversation:', error);
        }
    });
}

// Create a new conversation
function createNewConversation() {
    console.log("Creating new conversation");
    $.ajax({
        url: '/conversation',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({}),
        success: function(response) {
            console.log("New conversation created:", response);
            currentConversationId = response.id;
            
            // Clear chat body
            const chatBody = document.getElementById('chatBody');
            chatBody.innerHTML = '';
            
            // Add welcome message
            const welcomeContainer = document.createElement('div');
            welcomeContainer.className = 'message-container bot-container';
            welcomeContainer.id = 'welcomeContainer';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            
            const welcomeMessage = document.createElement('div');
            welcomeMessage.className = 'message bot-message';
            welcomeMessage.id = 'welcomeMessage';
            
            messageContent.appendChild(welcomeMessage);
            welcomeContainer.appendChild(messageContent);
            chatBody.appendChild(welcomeContainer);
            
            // Add welcome message with typewriter effect
            const welcomeText = "Hello! I'm Arogga FAQ Assistant. How can I help you today?";
            typeWriter(welcomeMessage, welcomeText);
            
            // Refresh conversation list
            loadConversations();
            
            // Reset active state
            document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
        },
        error: function(error) {
            console.error('Error creating conversation:', error);
        }
    });
}

// Sidebar functionality
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
    const newChatBtn = document.querySelector('.new-chat-btn');
    
    // Toggle sidebar on desktop
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        
        // Change icon direction
        const icon = sidebarToggle.querySelector('i');
        if (sidebar.classList.contains('collapsed')) {
            icon.classList.remove('bi-chevron-left');
            icon.classList.add('bi-chevron-right');
        } else {
            icon.classList.remove('bi-chevron-right');
            icon.classList.add('bi-chevron-left');
        }
    });
    
    // Toggle sidebar on mobile
    mobileSidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });
    
    // New chat button
    newChatBtn.addEventListener('click', () => {
        createNewConversation();
        
        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
        }
    });
}

// Add a message to the UI
function addMessageToUI(message, isUser, animate = true) {
    const chatBody = document.getElementById('chatBody');
    
    // Create message container
    const messageContainer = document.createElement('div');
    messageContainer.className = isUser ? 'message-container user-container' : 'message-container bot-container';
    
    // Create message content
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = isUser ? 'message user-message' : 'message bot-message';
    
    // Add content
    if (isUser) {
        messageElement.textContent = message;
    } else if (animate) {
        // Use typewriter effect for bot messages
        typeWriter(messageElement, message);
    } else {
        messageElement.textContent = message;
    }
    
    // Append elements
    messageContent.appendChild(messageElement);
    messageContainer.appendChild(messageContent);
    chatBody.appendChild(messageContainer);
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Function to ask a question
function askQuestion(question) {
    // Clear the input field if it's a suggestion chip
    document.getElementById('questionInput').value = '';
    
    // Don't process empty questions
    if (!question.trim()) return;
    
    console.log("Asking question:", question);
    
    // Add user message to UI
    addMessageToUI(question, true);
    
    // Show loader
    document.getElementById('loader').style.display = 'block';
    
    // Send question to server
    sendQuestionToServer(question, currentConversationId);
}

// Send question to server
function sendQuestionToServer(question, conversationId = null) {
    console.log("Sending question to server. ConversationId:", conversationId);
    
    // If no conversation exists, create one first
    if (!conversationId) {
        $.ajax({
            url: '/conversation',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ title: question.substring(0, 30) + '...' }),
            success: function(response) {
                console.log("Created new conversation for question:", response);
                currentConversationId = response.id;
                
                // Now send the question with the new conversation ID
                sendQuestionWithConversation(question, currentConversationId);
                
                // Refresh conversation list
                loadConversations();
            },
            error: function(error) {
                console.error('Error creating conversation:', error);
                document.getElementById('loader').style.display = 'none';
            }
        });
    } else {
        // Use existing conversation
        sendQuestionWithConversation(question, conversationId);
    }
}

// Helper function to send question with conversation ID
function sendQuestionWithConversation(question, conversationId) {
    console.log("Sending question with conversation ID:", question, conversationId);
    
    const requestData = JSON.stringify({ 
        question: question,
        conversation_id: conversationId
    });
    
    console.log("Request data:", requestData);
    
    $.ajax({
        url: '/ask',
        type: 'POST',
        contentType: 'application/json',
        data: requestData,
        success: function(response) {
            console.log("Received response:", response);
            
            // Hide loader
            document.getElementById('loader').style.display = 'none';
            
            // Add bot response to UI
            addMessageToUI(response.answer, false);
            
            // Update conversation list
            loadConversations();
        },
        error: function(error) {
            console.error("Error from server:", error);
            document.getElementById('loader').style.display = 'none';
            addMessageToUI('Sorry, I encountered an error. Please try again later.', false);
        }
    });
}

// Function to submit a question
function submitQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (question) {
        askQuestion(question);
        questionInput.value = '';
    }
    
    return false;
}

// Initialize event listeners when the document is ready
$(document).ready(function() {
    console.log("Document ready, initializing Arogga FAQ Assistant");
    
    // Initialize theme
    initTheme();
    
    // Initialize sidebar
    initSidebar();
    
    // Load conversations
    loadConversations();
    
    // Create new conversation if none exists
    setTimeout(() => {
        if (!currentConversationId) {
            console.log("No current conversation, creating a new one");
            createNewConversation();
        }
    }, 500);
    
    // Form submission
    document.getElementById('questionForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitQuestion();
    });
    
    // Enter key in input field
    document.getElementById('questionInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitQuestion();
        }
    });
});
