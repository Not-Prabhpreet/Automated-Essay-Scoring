import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Layout/Navbar";
import Score from "./pages/Score";

// Home component (we can move this to its own file later)
const Home = () => (
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 className="text-4xl font-bold text-center text-blue-600">
      Essay Scoring System
    </h1>
    <p className="text-center mt-4 text-gray-600">
      Get instant feedback on your essays
    </p>
  </div>
);

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/score" element={<Score />} />
            {/* We can add more routes here later */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
