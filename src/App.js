import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const ChatApp = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [threadId, setThreadId] = useState('');
  const [chatStarted, setChatStarted] = useState(false);

  const handleStartNewChat = async () => {
    try {
      const response = await axios.post('http://localhost:5000/start_chat');
      setThreadId(response.data.thread_id);
      setChatHistory([]);
      setChatStarted(true);
    } catch (error) {
      console.error('Error starting new chat:', error);
    }
  };

  const handleSendMessage = async () => {
    if (message && threadId) {
      try {
        const response = await axios.post('http://localhost:5000/send_message', {
          session_id: threadId,
          message: message
        });
        setChatHistory(response.data.chatHistory);
        setMessage('');
      } catch (error) {
        console.error('Error sending message:', error);
      }
    }
  };

  return (
    <div className="chat-app">
      {!chatStarted && (
        <button className="start-chat-button" onClick={handleStartNewChat}>
          Start New Chat
        </button>
      )}

      {chatStarted && (
        <>
          <div className="chat-history">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.role.toLowerCase()}`}>
                <strong>{msg.role}: </strong>{msg.message}
              </div>
            ))}
          </div>
          <div className="message-input">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a message..."
            />
            <button onClick={handleSendMessage}>Send</button>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatApp;
