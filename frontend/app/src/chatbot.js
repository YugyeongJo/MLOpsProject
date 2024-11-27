import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import './chatbot.css';

const Chatbot = () => {
   const formatTime = (date) => {
       const hours = date.getHours();
       const minutes = date.getMinutes().toString().padStart(2, '0');
       const ampm = hours >= 12 ? '오후' : '오전';
       const formattedHours = hours % 12 || 12;
       return `${ampm} ${formattedHours}:${minutes}`;
   };
   
   const chatContainerRef = useRef(null);
   const [isOpen, setIsOpen] = useState(false);
   const [messages, setMessages] = useState([
       { 
           text: "안녕하세요! 새싹봇입니다 피부고민이 있으시군요, 언제든지 편하게 질문해주세요!", 
           isBot: true,
           time: formatTime(new Date())  
       }
   ]);
   const [input, setInput] = useState("");
   const [isLoading, setIsLoading] = useState(false);  

   useEffect(() => {
       if (chatContainerRef.current) {
           chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
       }
   }, [messages]);

   const handleSend = async (e) => {
       e.preventDefault();
       const time = formatTime(new Date());
       if (!input.trim()) return;
       
       setMessages(prev => [
           ...prev,
           { text: input, isBot: false, time: time }
       ]);
       
       setIsLoading(true); 
       
       try {
           const response = await fetch('http://localhost:8000/chat', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json',
               },
               body: JSON.stringify({ message: input })
           });

           if (!response.ok) {
               throw new Error('Network response was not ok');
           }

           const data = await response.json();
           
           setMessages(prev => [
               ...prev,
               { 
                   text: data.response || data.advice || "응답을 받지 못했습니다.", 
                   isBot: true, 
                   time: formatTime(new Date()) 
               }
           ]);
       } catch (error) {
           console.error('Error:', error);

           setMessages(prev => [
               ...prev,
               { 
                   text: "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", 
                   isBot: true, 
                   time: formatTime(new Date()) 
               }
           ]);
       } finally {
           setIsLoading(false);  
           setInput("");  
       }
   };

   return (
       <div style={{ position: 'relative' }}>
           <button
               className="chatbot-button"
               onClick={() => setIsOpen(true)}
           >
               <img 
                   src={process.env.PUBLIC_URL + "/image/chatbot.png"} 
                   alt="Chatbot" 
                   className="chatbot-image"
               />
           </button>

           {isOpen && (
               <div className="modal-overlay">
                   <div className="modal-container">
                       <div className="chat-header">
                           <h3 className="chat-title">🌱새싹챗봇🌱</h3>
                           <button
                               onClick={() => setIsOpen(false)}
                               className="close-button"
                           >
                               <X />
                           </button>
                       </div>

                       <div className="chat-container" ref={chatContainerRef}>
                           {messages.map((message, index) => (
                               <div
                                   key={index}
                                   className="message-wrapper"
                               >
                                   <div
                                       className={message.isBot ? 'bot-message' : 'user-message'}
                                   >
                                       {message.text}
                                   </div>
                                   <span className="message-time">{message.time}</span>
                               </div>
                           ))}
                           {isLoading && (  
                               <div className="message-wrapper">
                                   <div className="bot-message">
                                       답변을 생성중입니다...
                                   </div>
                               </div>
                           )}
                       </div>

                       <form onSubmit={handleSend} className="input-form">
                           <div className="input-container">
                               <input
                                   type="text"
                                   value={input}
                                   onChange={(e) => setInput(e.target.value)}
                                   placeholder="메시지를 입력하세요..."
                                   className="chat-input"
                                   disabled={isLoading} 
                               />
                               <button
                                   type="submit"
                                   className="send-button"
                                   disabled={isLoading} 
                               >
                                   <Send />
                               </button>
                           </div>
                       </form>
                   </div>
               </div>
           )}
       </div>
   );
};

export default Chatbot;