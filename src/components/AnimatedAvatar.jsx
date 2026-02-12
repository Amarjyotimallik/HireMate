import { useEffect, useState } from 'react';

/**
 * AnimatedAvatar - A professional avatar with smooth CSS animations
 * Replace the image URL below with your own professional avatar image
 */
const AnimatedAvatar = ({ variant = 'login' }) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setIsVisible(true), 200);
        return () => clearTimeout(timer);
    }, []);

    // 👇 PASTE YOUR IMAGE URL HERE 👇
    const avatarImageUrl = "https://res.cloudinary.com/dw8s2k0a6/image/upload/v1770830451/Whisk_4021927937b13a796bd4794c562a8d00dr_bahdyq.png";

    return (
        <div className={`relative flex items-center justify-center transition-all duration-700 ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`}>
            {/* Outer blob shape */}
            <div className="absolute w-[480px] h-[480px] animate-avatar-blob">
                <svg viewBox="0 0 340 340" className="w-full h-full">
                    <defs>
                        <linearGradient id="blobGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor={variant === 'login' ? '#3B82F6' : '#8B5CF6'} stopOpacity="0.8" />
                            <stop offset="100%" stopColor={variant === 'login' ? '#1D4ED8' : '#6D28D9'} stopOpacity="0.6" />
                        </linearGradient>
                    </defs>
                    <path
                        d="M170,30 C250,30 310,80 310,170 C310,260 250,320 170,310 C90,300 30,260 30,170 C30,80 90,30 170,30 Z"
                        fill="url(#blobGradient)"
                        className="animate-avatar-morph"
                    />
                </svg>
            </div>

            {/* Inner circle background */}
            <div className="absolute w-[400px] h-[400px] rounded-full animate-avatar-scale-pulse"
                style={{
                    background: variant === 'login'
                        ? 'radial-gradient(circle, rgba(191, 219, 254, 0.9) 0%, rgba(147, 197, 253, 0.7) 100%)'
                        : 'radial-gradient(circle, rgba(221, 214, 254, 0.9) 0%, rgba(196, 181, 253, 0.7) 100%)'
                }}
            />

            {/* Main floating container with IMAGE - LARGER SIZE */}
            <div className="relative animate-avatar-float z-10">
                <img
                    src={avatarImageUrl}
                    alt="Professional Avatar"
                    className="w-[350px] h-[350px] object-cover rounded-full drop-shadow-2xl bg-white p-4"
                />
            </div>

            {/* Briefcase Icon - floating */}
            <div className="absolute right-2 top-1/4 animate-avatar-icon-float z-20">
                <div className="w-10 h-10 bg-white rounded-xl shadow-lg flex items-center justify-center border border-gray-100">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                        <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
                        <line x1="12" y1="12" x2="12" y2="12.01" />
                    </svg>
                </div>
            </div>

            {/* Sparkle elements */}
            <div className="absolute top-6 left-8 animate-avatar-sparkle">
                <svg width="16" height="16" viewBox="0 0 24 24" fill={variant === 'login' ? '#FBBF24' : '#A78BFA'}>
                    <path d="M12 0L14.59 8.41L23 12L14.59 15.59L12 24L9.41 15.59L1 12L9.41 8.41Z" />
                </svg>
            </div>
            <div className="absolute bottom-16 right-4 animate-avatar-sparkle" style={{ animationDelay: '1s' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill={variant === 'login' ? '#60A5FA' : '#C4B5FD'}>
                    <path d="M12 0L14.59 8.41L23 12L14.59 15.59L12 24L9.41 15.59L1 12L9.41 8.41Z" />
                </svg>
            </div>
            <div className="absolute top-16 right-16 animate-avatar-sparkle" style={{ animationDelay: '2s' }}>
                <svg width="10" height="10" viewBox="0 0 24 24" fill={variant === 'login' ? '#93C5FD' : '#DDD6FE'}>
                    <path d="M12 0L14.59 8.41L23 12L14.59 15.59L12 24L9.41 15.59L1 12L9.41 8.41Z" />
                </svg>
            </div>

            {/* Small floating circles */}
            <div className="absolute -top-2 right-12 w-4 h-4 rounded-full animate-avatar-particle"
                style={{ background: variant === 'login' ? '#93C5FD' : '#C4B5FD', animationDelay: '0s' }} />
            <div className="absolute bottom-20 left-4 w-3 h-3 rounded-full animate-avatar-particle"
                style={{ background: variant === 'login' ? '#60A5FA' : '#A78BFA', animationDelay: '1.5s' }} />
            <div className="absolute top-1/3 -right-2 w-2 h-2 rounded-full animate-avatar-particle"
                style={{ background: variant === 'login' ? '#BFDBFE' : '#DDD6FE', animationDelay: '0.7s' }} />
        </div>
    );
};

export default AnimatedAvatar;
