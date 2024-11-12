import React, { useState, useRef, useEffect } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const essayTypes = [
  {
    id: 'custom',
    title: "Custom Topic",
    description: "Write an essay on your own topic"
  },
  {
    id: 1,
    title: "Persuasive Essay - Computers in Education",
    prompt: "Write a letter to your local newspaper in which you state your opinion on the effects computers have on people. Persuade the readers to agree with you.",
    wordRange: "300-600 words"
  },
  {
    id: 2,
    title: "Library Censorship",
    prompt: "Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials should be removed if they are found offensive?",
    wordRange: "250-500 words"
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
      const response = await fetch('http://localhost:8000/score', {
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
        {/* Essay Type Selection */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6 transition-colors duration-200">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Select Essay Type</h2>
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

          {/* Prompt Display */}
          {selectedEssay && essayType !== 'custom' && (
            <div className="mt-4 p-4 bg-blue-50 dark:bg-gray-700 rounded-md transition-colors duration-200">
              <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Writing Prompt:</h3>
              <p className="text-gray-700 dark:text-gray-300">{selectedEssay.prompt}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Suggested length: {selectedEssay.wordRange}</p>
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
                  : 'Your Essay'}
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
                <span>Recommended: 300-600 words</span>
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
            {essayType === 'custom' && (
              <div className="text-sm font-normal text-gray-600 dark:text-gray-400 mt-1">
                Topic: {customTopic}
              </div>
            )}
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