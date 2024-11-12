import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Brain, PenTool, CheckCircle, Star } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const Home = () => {
  const navigate = useNavigate();
  const heroRef = useRef(null);
  const headingRef = useRef(null);
  const subheadingRef = useRef(null);
  const ctaRef = useRef(null);
  const featuresRef = useRef(null);

  useEffect(() => {
    // Initial hero animations
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' }});
    
    tl.from(headingRef.current, {
      y: 50,
      opacity: 1,
      duration: 1
    })
    .from(subheadingRef.current, {
      y: 30,
      opacity: 1,
      duration: 1
    }, "-=0.5")
    .from(ctaRef.current, {
      y: 20,
      opacity: 1,
      duration: 0.8
    }, "-=0.5");

    // Features animation on scroll
    gsap.from('.feature-card', {
      scrollTrigger: {
        trigger: featuresRef.current,
        start: 'top center+=100',
        toggleActions: 'play none none none'
      },
      y: 50,
      opacity: 2,
      duration: 0.8,
      stagger: 0.2
    });

    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Scoring",
      description: "Advanced machine learning algorithms evaluate your essays with human-like precision"
    },
    {
      icon: PenTool,
      title: "Detailed Feedback",
      description: "Get comprehensive feedback on grammar, structure, and content"
    },
    {
      icon: CheckCircle,
      title: "Instant Results",
      description: "Receive your score and feedback within seconds"
    },
    {
      icon: Star,
      title: "Multiple Essay Types",
      description: "Support for various essay types and custom topics"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero Section */}
      <div 
        ref={heroRef}
        className="relative px-4 pt-20 pb-16 sm:px-6 lg:px-8 lg:pt-32"
      >
        <div className="max-w-4xl mx-auto text-center">
          <h1 
            ref={headingRef}
            className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl"
          >
            Elevate Your Writing with
            <span className="block text-blue-600">AI-Powered Essay Scoring</span>
          </h1>
          
          <p 
            ref={subheadingRef}
            className="mt-6 text-xl leading-8 text-gray-600"
          >
            Get instant, professional-grade feedback on your essays using advanced machine learning technology.
          </p>

          <div 
            ref={ctaRef}
            className="mt-10 flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button
              onClick={() => navigate('/score')}
              className="inline-flex items-center px-6 py-3 text-lg font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors duration-200"
            >
              Score Your Essay
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
            <button
              onClick={() => navigate('/about')}
              className="inline-flex items-center px-6 py-3 text-lg font-semibold text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors duration-200"
            >
              Learn More
            </button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div 
        ref={featuresRef}
        className="py-24 sm:py-32 bg-white"
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center mb-16">
            <h2 className="text-base font-semibold leading-7 text-blue-600">
              Powerful Features
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to improve your writing
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-2">
              {features.map((feature, index) => (
                <div key={index} className="feature-card flex flex-col bg-white rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-200">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <feature.icon className="h-5 w-5 flex-none text-blue-600" />
                    {feature.title}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-blue-50 py-16">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3 text-center">
            {[
              { value: "98%", label: "Accuracy Rate" },
              { value: "500k+", label: "Essays Analyzed" },
              { value: "<2s", label: "Processing Time" }
            ].map((stat, index) => (
              <div key={index} className="feature-card bg-white rounded-lg p-8 shadow-lg">
                <div className="text-4xl font-bold text-blue-600">{stat.value}</div>
                <div className="mt-2 text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;