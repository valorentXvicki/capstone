import React, { useState } from 'react';

const messagesInitial = [
    { sender: 'bot', text: 'Welcome! Are you an athlete or a coach?' }
];

function Chatbot() {
    const [messages, setMessages] = useState(messagesInitial);
    const [input, setInput] = useState('');

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages([...messages, { sender: 'user', text: input }]);
        // Simple bot logic
        let botReply = '';
        if (/athlete/i.test(input)) {
            botReply = 'Great! How can I help you with your training today?';
        } else if (/coach/i.test(input)) {
            botReply = 'Hello Coach! What do you need assistance with?';
        } else {
            botReply = 'Tell me more about your goals or questions.';
        }
        setTimeout(() => {
            setMessages(msgs => [...msgs, { sender: 'bot', text: botReply }]);
        }, 500);
        setInput('');
    };

    return (
        <div style={{ maxWidth: 400, margin: 'auto', fontFamily: 'sans-serif' }}>
            <h2>Sports Chatbot</h2>
            <div style={{ border: '1px solid #ccc', padding: 10, height: 300, overflowY: 'auto', marginBottom: 10 }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '5px 0' }}>
                        <span style={{
                            display: 'inline-block',
                            background: msg.sender === 'user' ? '#007bff' : '#eee',
                            color: msg.sender === 'user' ? '#fff' : '#333',
                            borderRadius: 10,
                            padding: '6px 12px',
                            maxWidth: '80%',
                        }}>
                            {msg.text}
                        </span>
                    </div>
                ))}
            </div>
            <div>
                <input
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSend()}
                    placeholder="Type your message..."
                    style={{ width: '80%', padding: 8 }}
                />
                <button onClick={handleSend} style={{ padding: 8, marginLeft: 5 }}>Send</button>
            </div>
        </div>
    );
}

export default Chatbot;