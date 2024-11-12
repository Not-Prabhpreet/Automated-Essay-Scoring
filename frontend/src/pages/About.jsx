import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const About = () => {
  const titleRef = useRef(null);
  const sectionsRef = useRef([]);

  useEffect(() => {
    // Set initial states
    gsap.set(titleRef.current, {
      opacity: 0,
      y: 50
    });

    gsap.set(sectionsRef.current, {
      opacity: 0,
      y: 50
    });

    // Animate title
    gsap.to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 1,
      ease: 'power3.out'
    });

    // Animate sections
    gsap.to(sectionsRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.8,
      stagger: 0.2,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: sectionsRef.current,
        start: 'top center+=100',
        toggleActions: 'play none none reverse'
      }
    });

    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  const addToRefs = (el) => {
    if (el && !sectionsRef.current.includes(el)) {
      sectionsRef.current.push(el);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 transition-colors duration-200">
        <h1 
          ref={titleRef}
          className="text-3xl font-bold text-center mb-6 text-gray-900 dark:text-white opacity-0"
        >
          About Essay Scorer
        </h1>
        
        <div className="space-y-6">
          <div ref={addToRefs} className="opacity-0 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-all duration-200">
            <h2 className="text-xl font-semibold mb-3 text-blue-600 dark:text-blue-400">What is Essay Scorer?</h2>
            <p className="text-gray-600 dark:text-gray-300">
              Essay Scorer is an AI-powered essay evaluation system that provides instant, detailed feedback on your writing. 
              Using advanced machine learning algorithms, it analyzes various aspects of your essay including grammar, 
              coherence, and argumentation.
            </p>
          </div>

          <div ref={addToRefs} className="opacity-0 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-all duration-200">
            <h2 className="text-xl font-semibold mb-3 text-blue-600 dark:text-blue-400">How it Works</h2>
            <p className="text-gray-600 dark:text-gray-300">
              Our system combines multiple AI models including Random Forest and LSTM networks to provide comprehensive 
              analysis of your essays. The scores are normalized on a scale of 0-10 for consistency across different 
              essay types.
            </p>
          </div>

          <div ref={addToRefs} className="opacity-0 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-all duration-200">
            <h2 className="text-xl font-semibold mb-3 text-blue-600 dark:text-blue-400">Features</h2>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
              <li>Instant scoring and feedback</li>
              <li>Multiple essay types supported</li>
              <li>Detailed grammar and style analysis</li>
              <li>Custom topic support</li>
              <li>Comprehensive feedback system</li>
            </ul>
          </div>

          <div ref={addToRefs} className="opacity-0 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-all duration-200">
            <h2 className="text-xl font-semibold mb-3 text-blue-600 dark:text-blue-400">Technology</h2>
            <p className="text-gray-600 dark:text-gray-300">
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