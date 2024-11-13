import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Brain, PenTool, CheckCircle, Star } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import AnimatedButton from '../components/Layout/AnimatedButton';


gsap.registerPlugin(ScrollTrigger);

const Home = () => {
  const navigate = useNavigate();
  const heroRef = useRef(null);
  const headingRef = useRef(null); 
  const subheadingRef = useRef(null);
  const ctaRef = useRef(null);
  const featuresRef = useRef(null);

  useEffect(() => {
    // Set initial states first
    gsap.set([headingRef.current, subheadingRef.current, ctaRef.current], {
      opacity: 0,
      y: 50
    });
  
    gsap.set('.feature-card', {
      opacity: 0,
      y: 50
    });
  
    // Initial hero animations
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' }});
    
    tl.to(headingRef.current, {
      y: 0,
      opacity: 1,
      duration: 1
    })
    .to(subheadingRef.current, {
      y: 0,
      opacity: 1,
      duration: 1
    }, "-=0.7")
    .to(ctaRef.current, {
      y: 0,
      opacity: 1,
      duration: 0.8
    }, "-=0.7");
  
    // Features animation on scroll
    gsap.to('.feature-card', {
      scrollTrigger: {
        trigger: featuresRef.current,
        start: 'top center+=100',
        toggleActions: 'play none none reverse'
      },
      y: 0,
      opacity: 1,
      duration: 0.8,
      stagger: 0.2
    });
  
    // Stats animation
    gsap.to('.stat-card', {
      scrollTrigger: {
        trigger: '.stat-section',
        start: 'top center+=100',
        toggleActions: 'play none none reverse'
      },
      y: 0,
      opacity: 1,
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
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 transition-colors duration-200">
      {/* Hero Section */}
      <div 
        ref={heroRef}
        className="relative px-4 pt-20 pb-16 sm:px-6 lg:px-8 lg:pt-32"
      >
        <div className="max-w-4xl mx-auto text-center">
          <h1 
            ref={headingRef}
            className="text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl opacity-0"
          >
            Elevate Your Writing with
            <span className="block text-blue-600 dark:text-blue-400">AI-Powered Essay Scoring</span>
          </h1>
          
          <p 
            ref={subheadingRef}
            className="mt-6 text-xl leading-8 text-gray-600 dark:text-gray-300 opacity-0"
          >
            Get instant, professional-grade feedback on your essays using advanced machine learning technology.
          </p>

          <div ref={ctaRef} className="mt-10 flex flex-col sm:flex-row gap-4 justify-center opacity-0">
  <AnimatedButton 
    to="/score" 
    variant="primary"
    icon={ArrowRight}
  >
    Score Your Essay
  </AnimatedButton>
  
  <AnimatedButton 
    to="/about" 
    variant="secondary"
  >
    Learn More
  </AnimatedButton>
    </div>
        </div>
      </div>

      {/* Features Section */}
      <div 
        ref={featuresRef}
        className="py-24 sm:py-32 bg-white dark:bg-gray-900 transition-colors duration-200"
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center mb-16">
            <h2 className="text-base font-semibold leading-7 text-blue-600 dark:text-blue-400">
              Powerful Features
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              Everything you need to improve your writing
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-2">
              {features.map((feature, index) => (
                <div key={index} className="feature-card opacity-0 flex flex-col bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-all duration-200">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900 dark:text-white">
                    <feature.icon className="h-5 w-5 flex-none text-blue-600 dark:text-blue-400" />
                    {feature.title}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600 dark:text-gray-300">
                    <p className="flex-auto">{feature.description}</p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-blue-50 dark:bg-gray-800 py-16 stat-section transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3 text-center">
            {[
              { value: "98%", label: "Accuracy Rate" },
              { value: "500k+", label: "Essays Analyzed" },
              { value: "<2s", label: "Processing Time" }
            ].map((stat, index) => (
              <div 
                key={index} 
                className="stat-card bg-white dark:bg-gray-700 rounded-lg p-8 shadow-lg transform hover:scale-105 transition-all duration-200 opacity-0"
              >
                <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">{stat.value}</div>
                <div className="mt-2 text-gray-600 dark:text-gray-300">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;