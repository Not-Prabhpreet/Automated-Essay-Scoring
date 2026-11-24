import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Footer, Navbar, ScrollToTop } from './components/Layout';
import Home from './pages/Home';
import Grade from './pages/Grade';
import HowItWorks from './pages/HowItWorks';

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/grade" element={<Grade />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            {/* old paths */}
            <Route path="/score" element={<Navigate to="/grade" replace />} />
            <Route path="/about" element={<Navigate to="/how-it-works" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
