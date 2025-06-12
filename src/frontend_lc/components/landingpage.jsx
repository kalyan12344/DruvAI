import React from 'react';
import Header from './header';
import HeroSection from './hero';
import '../styles/landingpage.css'; // Assuming you have a CSS file for styling the landing page

const LandingPage = () => {
    return (
        <div className="landing-page">
            <Header />
            <HeroSection />
        </div>
    );
};

export default LandingPage;