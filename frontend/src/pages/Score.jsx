import React, { useState, useRef, useEffect } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const essayTypes = [
  {
    id: 'custom',
    title: "Custom Topic",
    description: "Write an essay on your chosen topic",
    prompt: "Write a well-structured essay with clear arguments and supporting evidence.",
    wordRange: "300-600 words",
    scoringInfo: "Your essay will be evaluated on content, organization, and language conventions.",
    type: "Open Format"
  },
  {
    id: '1',
    title: "Social Media and Mental Health",
    prompt: "Discuss how social media affects mental well-being in today's society. Consider both positive and negative impacts.",
    wordRange: "350-600 words",
    scoringInfo: "Focus on developing clear arguments with specific examples and real-world evidence to support your position.",
    type: "Persuasive Essay"
  },
  {
    id: '2',
    title: "Online Education vs Traditional Classrooms",
    prompt: "Compare and contrast online learning with traditional classroom education. Which method do you think is more effective and why?",
    wordRange: "350-600 words",
    scoringInfo: "Present balanced arguments, use specific examples, and consider multiple perspectives.",
    type: "Argumentative Essay"
  },
  {
    id: '3',
    title: "Impact of Artificial Intelligence",
    prompt: "How is AI technology affecting various aspects of our daily lives? Is this impact more beneficial or harmful to society overall?",
    wordRange: "350-600 words",
    scoringInfo: "Support your position with concrete examples and consider both advantages and disadvantages.",
    type: "Analytical Essay"
  },
  {
    id: '4',
    title: "Environmental Responsibility",
    prompt: "What role should individuals play in addressing environmental challenges? Discuss specific actions and their potential impact.",
    wordRange: "400-650 words",
    scoringInfo: "Provide specific solutions, explain their feasibility, and discuss their potential effectiveness.",
    type: "Persuasive Essay"
  }
];

const Score = () => {
  const [loading, setLoading] = useState(false);
  const [essayType, setEssayType] = useState('custom');
  const [customTopic, setCustomTopic] = useState('');
  const [essayText, setEssayText] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const formRef = useRef(null);
  const resultRef = useRef(null);

  const wordCount = essayText.trim().split(/\s+/).filter(Boolean).length;
  const selectedEssay = essayTypes.find(type => type.id === essayType);
  useEffect(() => {
    gsap.set(formRef.current, {
      opacity: 0,
      y: 50
    });

    gsap.to(formRef.current, {
      opacity: 1,
      y: 0,
      duration: 1,
      ease: 'power3.out'
    });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (essayType === 'custom' && !customTopic.trim()) {
      setError('Please enter your essay topic');
      return;
    }
    const loadingTl = gsap.timeline();
    loadingTl.to(formRef.current, {
      opacity: 0.7,
      scale: 0.99,
      duration: 0.3
    });
    setLoading(true);
    setError('');

    try {
      // Update this in Score.jsx
      const API_URL = "https://essay-scorer-backend.onrender.com";  // Your actual backend URL'  // replace with your actual render URL

      // Then update your fetch call
      const response = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          essay: essayText,
          essay_set: essayType === 'custom' ? 1 : parseInt(essayType)
        })
      });

      if (!response.ok) {
        throw new Error('Failed to score essay');
      }

      const data = await response.json();
      setResult(data);
      loadingTl.to(formRef.current, {
        opacity: 1,
        scale: 1,
        duration: 0.3
      });

      if (resultRef.current) {
        gsap.fromTo(resultRef.current,
          { opacity: 0, y: 50 },
          { 
            opacity: 1, 
            y: 0, 
            duration: 0.8,
            scrollTrigger: {
              trigger: resultRef.current,
              start: 'top center+=100'
            }
          }
        );
      }
    } catch (err) {
      setError(err.message);
      loadingTl.to(formRef.current, {
        opacity: 1,
        scale: 1,
        duration: 0.3
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-200">
      <div ref={formRef} className="opacity-0">
        {/* Essay Topic Selection */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6 transition-colors duration-200">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Choose Your Essay Topic</h2>
          <select
            value={essayType}
            onChange={(e) => {
              setEssayType(e.target.value);
              if (e.target.value !== 'custom') {
                setCustomTopic('');
              }
            }}
            className="w-full p-2 border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400"
          >
            {essayTypes.map(type => (
              <option key={type.id} value={type.id}>
                {type.title}
              </option>
            ))}
          </select>
          {/* Custom Topic Input */}
          {essayType === 'custom' && (
            <div className="mt-4">
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Your Essay Topic</label>
              <input
                type="text"
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                className="w-full p-2 border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400"
                placeholder="Enter your essay topic"
              />
            </div>
          )}

          {/* Topic Information Display */}
          {selectedEssay && (
            <div className="mt-6 space-y-4">
              <div className="p-4 bg-blue-50 dark:bg-gray-700 rounded-md transition-colors duration-200">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Writing Prompt:</h3>
                <p className="text-gray-700 dark:text-gray-300">{selectedEssay.prompt}</p>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">
                    Word Range: {selectedEssay.wordRange}
                  </span>
                  {selectedEssay.type && (
                    <span className="text-gray-500 dark:text-gray-400">
                      Type: {selectedEssay.type}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Scoring Guidelines:</h3>
                <p className="text-gray-700 dark:text-gray-300">{selectedEssay.scoringInfo}</p>
              </div>
            </div>
          )}
        </div>

        {/* Essay Input */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 transition-colors duration-200">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                {essayType === 'custom' 
                  ? `Your Essay on "${customTopic || 'Your Topic'}"` 
                  : `Your Essay on "${selectedEssay.title}"`}
              </label>
              <textarea
                value={essayText}
                onChange={(e) => setEssayText(e.target.value)}
                className="w-full h-64 p-4 border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400"
                placeholder={essayType === 'custom' 
                  ? "Write your essay here..."
                  : `Write your essay addressing the prompt above...`}
                required
              />
              <div className="mt-2 flex justify-between text-sm text-gray-500 dark:text-gray-400">
                <span>Word count: {wordCount}</span>
                <span>Recommended: {selectedEssay.wordRange}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !essayText.trim() || (essayType === 'custom' && !customTopic.trim())}
              className={`w-full py-3 rounded-md text-white font-medium transition-colors duration-200 ${
                loading || !essayText.trim() || (essayType === 'custom' && !customTopic.trim())
                  ? 'bg-blue-300 dark:bg-blue-700'
                  : 'bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600'
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <Loader2 className="animate-spin mr-2" />
                  Analyzing Essay...
                </span>
              ) : (
                'Score My Essay'
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Results Display */}
      {result && (
        <div ref={resultRef} className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 opacity-0 transition-colors duration-200">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-900 dark:text-white">
            Essay Score
            <div className="text-sm font-normal text-gray-600 dark:text-gray-400 mt-1">
              Topic: {essayType === 'custom' ? customTopic : selectedEssay.title}
            </div>
          </h2>
          
          <div className="text-5xl font-bold text-center text-blue-600 dark:text-blue-400 mb-8">
            {result.score.toFixed(1)}/10
          </div>

          <div className="space-y-6">
            {Object.entries(result.feedback).map(([category, points]) => (
              <div key={category} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 transition-colors duration-200">
                <h3 className="font-semibold text-lg capitalize mb-2 text-gray-900 dark:text-white">{category}</h3>
                <ul className="list-disc list-inside space-y-2">
                  {points.map((point, index) => (
                    <li key={index} className="text-gray-700 dark:text-gray-300">{point}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-md flex items-center transition-colors duration-200">
          <AlertCircle className="mr-2" />
          {error}
        </div>
      )}
    </div>
  );
};

export default Score;