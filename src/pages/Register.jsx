import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    Mail,
    Lock,
    Eye,
    EyeOff,
    ArrowRight,
    Sparkles,
    User,
    Building2,
    Phone,
    CheckCircle,
    Shield,
    Users,
    Zap,
    AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AnimatedAvatar from '../components/AnimatedAvatar';

const Register = () => {
    const navigate = useNavigate();
    const { register, redirectPath } = useAuth();
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [currentStep, setCurrentStep] = useState(1);
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        companyName: '',
        companySize: '',
        password: '',
        confirmPassword: '',
        agreeToTerms: false
    });
    const [errors, setErrors] = useState({});
    const [apiError, setApiError] = useState('');

    const companySizes = [
        '1-10 employees',
        '11-50 employees',
        '51-200 employees',
        '201-500 employees',
        '500+ employees'
    ];

    const benefits = [
        {
            icon: Zap,
            title: 'Quick Setup',
            description: 'Get started in minutes with our intuitive onboarding'
        },
        {
            icon: Users,
            title: 'Unlimited Candidates',
            description: 'No limits on the number of candidates you can assess'
        },
        {
            icon: Shield,
            title: 'Free 14-Day Trial',
            description: 'Full access to all features, no credit card required'
        }
    ];

    const passwordRequirements = [
        { text: 'At least 8 characters', met: formData.password.length >= 8 },
        { text: 'One uppercase letter', met: /[A-Z]/.test(formData.password) },
        { text: 'One lowercase letter', met: /[a-z]/.test(formData.password) },
        { text: 'One number', met: /\d/.test(formData.password) }
    ];

    const validateStep1 = () => {
        const newErrors = {};

        if (!formData.firstName.trim()) {
            newErrors.firstName = 'First name is required';
        }

        if (!formData.lastName.trim()) {
            newErrors.lastName = 'Last name is required';
        }

        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email';
        }

        if (!formData.phone) {
            newErrors.phone = 'Phone number is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const validateStep2 = () => {
        const newErrors = {};

        if (!formData.companyName.trim()) {
            newErrors.companyName = 'Company name is required';
        }

        if (!formData.companySize) {
            newErrors.companySize = 'Please select company size';
        }

        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters';
        } else if (!/[A-Z]/.test(formData.password) || !/[a-z]/.test(formData.password) || !/\d/.test(formData.password)) {
            newErrors.password = 'Password must meet all requirements';
        }

        if (!formData.confirmPassword) {
            newErrors.confirmPassword = 'Please confirm your password';
        } else if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }

        if (!formData.agreeToTerms) {
            newErrors.agreeToTerms = 'You must agree to the terms';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validateStep1()) {
            setCurrentStep(2);
        }
    };

    const handleBack = () => {
        setCurrentStep(1);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setApiError('');

        if (!validateStep2()) return;

        setIsLoading(true);

        try {
            await register({
                email: formData.email,
                full_name: `${formData.firstName} ${formData.lastName}`,
                password: formData.password,
            });
            navigate(redirectPath || '/dashboard');
        } catch (err) {
            // Provide user-friendly error messages
            let errorMessage = err.message || 'Registration failed. Please try again.';
            if (err.status === 409 || err.message?.includes('already exists') || err.message?.includes('duplicate')) {
                errorMessage = 'An account with this email already exists. Please log in instead.';
            } else if (err.status === 400) {
                errorMessage = err.json?.detail || 'Invalid registration data. Please check your information.';
            } else if (err.status === 0 || !navigator.onLine) {
                errorMessage = 'No internet connection. Please check your network.';
            } else if (err.status >= 500) {
                errorMessage = 'Server error. Please try again later.';
            }
            setApiError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));

        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    return (
        <div className="min-h-screen flex">
            {/* Left Panel - Branding */}
            <div className="hidden lg:flex lg:w-2/5 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 relative overflow-hidden">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-20 left-10 w-64 h-64 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute bottom-32 right-10 w-80 h-80 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-white rounded-full blur-3xl opacity-5"></div>
                </div>

                {/* Animated Shapes */}
                <div className="absolute top-24 right-12 w-16 h-16 bg-white/10 rounded-2xl backdrop-blur-lg animate-float"></div>
                <div className="absolute bottom-24 left-12 w-12 h-12 bg-white/10 rounded-xl backdrop-blur-lg animate-float" style={{ animationDelay: '1.5s' }}></div>
                <div className="absolute top-1/3 right-24 w-8 h-8 bg-white/10 rounded-lg backdrop-blur-lg animate-float" style={{ animationDelay: '0.5s' }}></div>

                {/* Content */}
                <div className="relative z-10 flex flex-col items-center justify-center px-10 xl:px-16 w-full">
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <img
                            src="/hiremate-logo.svg"
                            alt="HireMate Logo"
                            className="w-12 h-12"
                        />
                        <span className="text-3xl font-bold text-white">HireMate</span>
                    </div>

                    {/* Animated Avatar */}
                    <div className="mb-8">
                        <AnimatedAvatar variant="register" />
                    </div>

                    {/* Headline */}
                    <h1 className="text-3xl font-bold text-white mb-3 leading-tight text-center">
                        Start Hiring<br />
                        <span className="text-purple-200">Smarter Today</span>
                    </h1>

                    <p className="text-base text-purple-100 mb-6 max-w-sm text-center">
                        Join thousands of companies using HireMate to find and assess top talent.
                    </p>

                    {/* Benefits as compact pills */}
                    <div className="flex flex-wrap justify-center gap-3">
                        {benefits.map((benefit, index) => (
                            <div
                                key={index}
                                className="flex items-center gap-2 bg-white/10 backdrop-blur-lg rounded-full px-4 py-2"
                            >
                                <benefit.icon className="w-4 h-4 text-white" />
                                <span className="text-white text-sm font-medium">{benefit.title}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right Panel - Registration Form */}
            <div className="w-full lg:w-3/5 flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black px-6 py-8 overflow-y-auto">
                <div className="w-full max-w-lg">
                    {/* Mobile Logo */}
                    <div className="flex items-center justify-center gap-2 mb-6 lg:hidden">
                        <img
                            src="/hiremate-logo.svg"
                            alt="HireMate Logo"
                            className="w-10 h-10"
                        />
                        <span className="text-2xl font-bold text-gray-800 dark:text-white">HireMate</span>
                    </div>

                    {/* Progress Steps */}
                    <div className="flex items-center justify-center mb-8">
                        <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all duration-300 ${currentStep >= 1 ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white' : 'bg-gray-200 text-gray-500'
                                }`}>
                                {currentStep > 1 ? <CheckCircle className="w-5 h-5" /> : '1'}
                            </div>
                            <div className={`w-16 h-1 rounded-full transition-all duration-300 ${currentStep > 1 ? 'bg-gradient-to-r from-blue-600 to-indigo-600' : 'bg-gray-200'
                                }`}></div>
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all duration-300 ${currentStep >= 2 ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white' : 'bg-gray-200 text-gray-500'
                                }`}>
                                2
                            </div>
                        </div>
                    </div>

                    {/* Header */}
                    <div className="text-center mb-6">
                        <h2 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
                            {currentStep === 1 ? 'Personal Information' : 'Company & Security'}
                        </h2>
                        <p className="text-gray-600 dark:text-gray-400">
                            {currentStep === 1
                                ? 'Tell us about yourself to get started'
                                : 'Complete your account setup'}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* API Error Message */}
                        {apiError && (
                            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400 text-sm animate-fade-in">
                                <div className="flex items-start gap-2">
                                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                    <span>{apiError}</span>
                                </div>
                            </div>
                        )}
                        {currentStep === 1 ? (
                            <>
                                {/* Name Fields */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                            First Name
                                        </label>
                                        <div className="relative">
                                            <User className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                            <input
                                                type="text"
                                                id="firstName"
                                                name="firstName"
                                                value={formData.firstName}
                                                onChange={handleChange}
                                                className={`w-full pl-12 pr-4 py-3.5 bg-white border ${errors.firstName ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                                placeholder="John"
                                            />
                                        </div>
                                        {errors.firstName && (
                                            <p className="mt-1.5 text-sm text-red-500">{errors.firstName}</p>
                                        )}
                                    </div>
                                    <div>
                                        <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                            Last Name
                                        </label>
                                        <div className="relative">
                                            <User className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                            <input
                                                type="text"
                                                id="lastName"
                                                name="lastName"
                                                value={formData.lastName}
                                                onChange={handleChange}
                                                className={`w-full pl-12 pr-4 py-3.5 bg-white border ${errors.lastName ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                                placeholder="Doe"
                                            />
                                        </div>
                                        {errors.lastName && (
                                            <p className="mt-1.5 text-sm text-red-500">{errors.lastName}</p>
                                        )}
                                    </div>
                                </div>

                                {/* Email Field */}
                                <div>
                                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                        Work Email
                                    </label>
                                    <div className="relative">
                                        <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            type="email"
                                            id="email"
                                            name="email"
                                            value={formData.email}
                                            onChange={handleChange}
                                            className={`w-full pl-12 pr-4 py-3.5 bg-white border ${errors.email ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                            placeholder="john@company.com"
                                        />
                                    </div>
                                    {errors.email && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.email}</p>
                                    )}
                                </div>

                                {/* Phone Field */}
                                <div>
                                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                        Phone Number
                                    </label>
                                    <div className="relative">
                                        <Phone className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            type="tel"
                                            id="phone"
                                            name="phone"
                                            value={formData.phone}
                                            onChange={handleChange}
                                            className={`w-full pl-12 pr-4 py-3.5 bg-white border ${errors.phone ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                            placeholder="+1 (555) 000-0000"
                                        />
                                    </div>
                                    {errors.phone && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.phone}</p>
                                    )}
                                </div>

                                {/* Next Button */}
                                <button
                                    type="button"
                                    onClick={handleNext}
                                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl active:scale-95 mt-6"
                                >
                                    <span>Continue</span>
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </>
                        ) : (
                            <>
                                {/* Company Name */}
                                <div>
                                    <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                        Company Name
                                    </label>
                                    <div className="relative">
                                        <Building2 className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            type="text"
                                            id="companyName"
                                            name="companyName"
                                            value={formData.companyName}
                                            onChange={handleChange}
                                            className={`w-full pl-12 pr-4 py-3.5 bg-white border ${errors.companyName ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                            placeholder="Your company name"
                                        />
                                    </div>
                                    {errors.companyName && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.companyName}</p>
                                    )}
                                </div>

                                {/* Company Size */}
                                <div>
                                    <label htmlFor="companySize" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                        Company Size
                                    </label>
                                    <select
                                        id="companySize"
                                        name="companySize"
                                        value={formData.companySize}
                                        onChange={handleChange}
                                        className={`w-full px-4 py-3.5 bg-white border ${errors.companySize ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white appearance-none cursor-pointer`}
                                    >
                                        <option value="">Select company size</option>
                                        {companySizes.map((size, index) => (
                                            <option key={index} value={size}>{size}</option>
                                        ))}
                                    </select>
                                    {errors.companySize && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.companySize}</p>
                                    )}
                                </div>

                                {/* Password Field */}
                                <div>
                                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                        Password
                                    </label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            id="password"
                                            name="password"
                                            value={formData.password}
                                            onChange={handleChange}
                                            className={`w-full pl-12 pr-12 py-3.5 bg-white border ${errors.password ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                            placeholder="Create a strong password"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-gray-400 transition-colors"
                                        >
                                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                        </button>
                                    </div>
                                    {errors.password && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.password}</p>
                                    )}

                                    {/* Password Requirements */}
                                    <div className="mt-3 grid grid-cols-2 gap-2">
                                        {passwordRequirements.map((req, index) => (
                                            <div key={index} className="flex items-center gap-2">
                                                <CheckCircle className={`w-4 h-4 ${req.met ? 'text-green-500' : 'text-gray-300'} transition-colors`} />
                                                <span className={`text-xs ${req.met ? 'text-green-600' : 'text-gray-500'}`}>{req.text}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Confirm Password Field */}
                                <div>
                                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                        Confirm Password
                                    </label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            type={showConfirmPassword ? 'text' : 'password'}
                                            id="confirmPassword"
                                            name="confirmPassword"
                                            value={formData.confirmPassword}
                                            onChange={handleChange}
                                            className={`w-full pl-12 pr-12 py-3.5 bg-white border ${errors.confirmPassword ? 'border-red-500' : 'border-gray-200'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                            placeholder="Confirm your password"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-gray-400 transition-colors"
                                        >
                                            {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                        </button>
                                    </div>
                                    {errors.confirmPassword && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.confirmPassword}</p>
                                    )}
                                </div>

                                {/* Terms Checkbox */}
                                <div>
                                    <label className="flex items-start gap-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            name="agreeToTerms"
                                            checked={formData.agreeToTerms}
                                            onChange={handleChange}
                                            className="w-5 h-5 mt-0.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-sm text-gray-600 dark:text-gray-400">
                                            I agree to the{' '}
                                            <a href="#" className="text-blue-600 hover:underline">Terms of Service</a>
                                            {' '}and{' '}
                                            <a href="#" className="text-blue-600 hover:underline">Privacy Policy</a>
                                        </span>
                                    </label>
                                    {errors.agreeToTerms && (
                                        <p className="mt-1.5 text-sm text-red-500">{errors.agreeToTerms}</p>
                                    )}
                                </div>

                                {/* Action Buttons */}
                                <div className="flex gap-4 mt-6">
                                    <button
                                        type="button"
                                        onClick={handleBack}
                                        className="flex-1 bg-gray-100 text-gray-700 dark:text-gray-200 font-semibold py-4 px-6 rounded-xl hover:bg-gray-200 transition-all duration-300 active:scale-95"
                                    >
                                        Back
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={isLoading}
                                        className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed active:scale-95"
                                    >
                                        {isLoading ? (
                                            <>
                                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                                <span>Creating...</span>
                                            </>
                                        ) : (
                                            <>
                                                <span>Create Account</span>
                                                <ArrowRight className="w-5 h-5" />
                                            </>
                                        )}
                                    </button>
                                </div>
                            </>
                        )}
                    </form>

                    {/* Sign In Link */}
                    <p className="text-center mt-6 text-gray-600 dark:text-gray-400">
                        Already have an account?{' '}
                        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold transition-colors">
                            Sign in
                        </Link>
                    </p>

                    {/* Security Badge */}
                    <div className="flex items-center justify-center gap-2 mt-6 text-gray-400">
                        <Shield className="w-4 h-4" />
                        <span className="text-xs">Your data is secured with enterprise-grade encryption</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;
