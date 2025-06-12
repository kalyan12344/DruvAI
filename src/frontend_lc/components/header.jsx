import React from 'react';
import '../styles/header.css';

const Header = () => {
    return (
        <>
            <div style={{ position: 'absolute', top: "-30%", left: 0, width: '100%', height: '100%', zIndex: -1 }}>
                <div className="circle-container">
                    <div className="inner-circle"></div>
                    <div className="outer-circle"></div>
                </div>
            </div>

            <header className="header">
                <div className="logo">
                    <div className="logo-circle"></div>
                    <span>Druv</span>
                </div>


                <nav >
                    <div className="nav">
                        <a href="#" className="nav-it">Use cases</a>
                        <a href="#" className="nav-it">Integrations</a>
                        <a href="#" className="nav-it">Customers</a>
                        <a href="#" className="nav-it">Pricing</a></div>
                </nav>

                <div className="signin-bt">Sign In</div>

            </header></>
    );
};

export default Header;