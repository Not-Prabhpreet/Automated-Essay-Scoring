import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';

const Score = () => {
  const [essayText, setEssayText] = useState('');
  const [essayType, setEssayType] = useState('1');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
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
          essay_set: parseInt(essayType)
        })
      });

      if (!response.ok) {
        throw new Error('Failed to score essay');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">
          Submit Your Essay
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Essay Type
            </label>
            <select
              value={essayType}
              onChange={(e) => setEssayType(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1">Persuasive Essay</option>
              <option value="2">Analytical Essay</option>
              <option value="3">Expository Essay</option>
              <option value="4">Narrative Essay</option>
              <option value="5">Descriptive Essay</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Essay
            </label>
            <textarea
              value={essayText}
              onChange={(e) => setEssayText(e.target.value)}
              placeholder="Enter your essay here..."
              rows={10}
              className="w-full rounded-md border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              Word count: {essayText.trim().split(/\s+/).filter(Boolean).length}
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !essayText.trim()}
            className="w-full py-3 px-4 rounded-md text-white font-medium bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors duration-200"
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

        {result && (
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold text-center mb-4">Essay Score</h3>
            
            <div className="text-5xl font-bold text-blue-600 text-center mb-6">
              {result.score.toFixed(1)}/10
            </div>

            {result.feedback && (
              <div className="space-y-4">
                <h4 className="text-lg font-semibold">Detailed Feedback</h4>
                {Object.entries(result.feedback).map(([category, points]) => (
                  <div key={category} className="bg-gray-50 rounded-lg p-4">
                    <h5 className="text-md font-medium capitalize mb-2">{category}</h5>
                    <ul className="list-disc list-inside space-y-1">
                      {points.map((point, index) => (
                        <li key={index} className="text-gray-600 text-sm">
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 text-red-600 p-4 rounded-md">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default Score;