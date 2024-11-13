import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Layout/NavBar';
import Footer from './components/Layout/Footer';
import Home from './pages/Home';
import Score from './pages/Score';
import About from './pages/About';
import CustomCursor from './components/Layout/CustomCursor';
import HoverText from './components/Layout/HoverText';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <CustomCursor />
        <Navbar />
        <h1>
  
      </h1>
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/score" element={<Score />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;