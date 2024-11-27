import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import FileUpload from './FileUpload';
import SkinResult from './SkinResult';
import Chatbot from './chatbot'

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<FileUpload />} />
          <Route path="/result" element={<SkinResult />} />
          <Route path="/chatbot" element={<Chatbot />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;