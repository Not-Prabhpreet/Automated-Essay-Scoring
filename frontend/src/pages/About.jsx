import React from 'react';

const About = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold text-center mb-6">About Essay Scorer</h1>
        
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold mb-3">What is Essay Scorer?</h2>
            <p className="text-gray-600">
              Essay Scorer is an AI-powered essay evaluation system that provides instant, detailed feedback on your writing. 
              Using advanced machine learning algorithms, it analyzes various aspects of your essay including grammar, 
              coherence, and argumentation.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">How it Works</h2>
            <p className="text-gray-600">
              Our system combines multiple AI models including Random Forest and LSTM networks to provide comprehensive 
              analysis of your essays. The scores are normalized on a scale of 0-10 for consistency across different 
              essay types.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">Features</h2>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>Instant scoring and feedback</li>
              <li>Multiple essay types supported</li>
              <li>Detailed grammar and style analysis</li>
              <li>Custom topic support</li>
              <li>Comprehensive feedback system</li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">Technology</h2>
            <p className="text-gray-600">
              Built using state-of-the-art machine learning technologies and natural language processing, 
              our system provides accurate and helpful feedback to help improve your writing skills.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;