import React from 'react';
import '../styles/hero.css';
import "../../assets/hero2.png"
import FeatureCards from './featurecards';
import CardStack from './featurecards';
import { useNavigate } from 'react-router-dom';

const HeroSection = () => {
    const navigate = useNavigate();

    const handlestart = () => {
        navigate('/dashboard');
    }

    return (
        <section className="hero">
            <div className="hero-content" style={{ marginTop: "30%" }}>
                <div className="heading">Level up your hustle</div>
                <div className="tagline">AI assistance for work, life, and everything in between</div>
                <button className="cta-btn" onClick={handlestart}>Start for free <img style={{ width: "20px" }} src='../../src//assets/star.png' /></button>
            </div>
            <div className="">
                <img className="hero-image"
                    src='../../src/assets/hero.png' />

            </div>
            <div class="chat-wrapper">
                <div class="chat-bubble">
                    <span class="bubble-gloss"></span>

                    <p>Hello there!<br />This is your AI assistant 😄</p>
                </div>
            </div>

            <CardStack />
            <div className="background-text">
                <span className="text-1">Personal</span>
                <span className="text-2">Assistant</span>
                <span className="text-3">AI</span>
            </div>
        </section>
    );
};

export default HeroSection;