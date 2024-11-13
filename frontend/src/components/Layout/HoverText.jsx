import React, { useRef, useEffect } from 'react';
import gsap from 'gsap';

const HoverText = ({ children, className }) => {
  const textRef = useRef(null);

  useEffect(() => {
    const element = textRef.current;
    
    const handleHover = () => {
      gsap.to(element, {
        color: '#60A5FA', // Change this to your preferred hover color
        duration: 0.3,
        ease: 'power2.out'
      });
    };

    const handleHoverOut = () => {
      gsap.to(element, {
        color: 'inherit',
        duration: 0.3,
        ease: 'power2.out'
      });
    };

    element.addEventListener('mouseenter', handleHover);
    element.addEventListener('mouseleave', handleHoverOut);

    return () => {
      element.removeEventListener('mouseenter', handleHover);
      element.removeEventListener('mouseleave', handleHoverOut);
    };
  }, []);

  return (
    <span ref={textRef} className={className}>
      {children}
    </span>
  );
};

export default HoverText;