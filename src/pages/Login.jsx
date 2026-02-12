import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    Mail,
    Lock,
    Eye,
    EyeOff,
    ArrowRight,
    Sparkles,
    Users,
    BarChart3,
    Shield,
    CheckCircle2,
    AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AnimatedAvatar from '../components/AnimatedAvatar';

const Login = () => {
    const navigate = useNavigate();
    const { login, redirectPath } = useAuth();
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        rememberMe: false
    });
    const [errors, setErrors] = useState({});
    const [apiError, setApiError] = useState('');

    const features = [
        {
            icon: Users,
            title: 'Smart Candidate Matching',
            description: 'AI-powered resume parsing and skill assessment'
        },
        {
            icon: BarChart3,
            title: 'Real-time Analytics',
            description: 'Track hiring metrics and candidate performance'
        },
        {
            icon: Shield,
            title: 'Secure & Reliable',
            description: 'Enterprise-grade security for your data'
        }
    ];

    const validateForm = () => {
        const newErrors = {};

        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email';
        }

        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setApiError('');

        if (!validateForm()) return;

        setIsLoading(true);

        try {
            await login(formData.email, formData.password);
            // Redirect to the saved path or dashboard
            navigate(redirectPath || '/dashboard');
        } catch (err) {
            // Provide user-friendly error messages
            let errorMessage = err.message || 'Login failed. Please check your credentials.';
            if (err.status === 401) {
                errorMessage = 'Invalid email or password. Please try again.';
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
            {/* Left Panel - Branding & Features */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 relative overflow-hidden">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-20 left-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-white rounded-full blur-3xl opacity-5"></div>
                </div>

                {/* Floating Elements */}
                <div className="absolute top-32 right-16 w-20 h-20 bg-white/10 rounded-2xl backdrop-blur-lg animate-float"></div>
                <div className="absolute bottom-32 left-16 w-16 h-16 bg-white/10 rounded-xl backdrop-blur-lg animate-float" style={{ animationDelay: '1s' }}></div>
                <div className="absolute top-1/2 right-32 w-12 h-12 bg-white/10 rounded-lg backdrop-blur-lg animate-float" style={{ animationDelay: '2s' }}></div>

                {/* Content */}
                <div className="relative z-10 flex flex-col items-center justify-center px-12 xl:px-20 w-full">
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
                        <AnimatedAvatar variant="login" />
                    </div>

                    {/* Headline */}
                    <h1 className="text-3xl xl:text-4xl font-bold text-white mb-3 leading-tight text-center">
                        Revolutionize Your<br />
                        <span className="text-blue-200">Hiring Process</span>
                    </h1>

                    <p className="text-base text-blue-100 mb-6 max-w-md text-center">
                        AI-powered assessments, real-time analytics, and seamless candidate management.
                    </p>

                    {/* Stats */}
                    <div className="flex gap-8">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-white">10K+</div>
                            <div className="text-blue-200 text-xs">Active Recruiters</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-white">50K+</div>
                            <div className="text-blue-200 text-xs">Candidates Assessed</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-white">98%</div>
                            <div className="text-blue-200 text-xs">Satisfaction Rate</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Panel - Login Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black px-6 py-12">
                <div className="w-full max-w-md">
                    {/* Mobile Logo */}
                    <div className="flex items-center justify-center gap-2 mb-8 lg:hidden">
                        <img
                            src="/hiremate-logo.svg"
                            alt="HireMate Logo"
                            className="w-10 h-10"
                        />
                        <span className="text-2xl font-bold text-gray-800 dark:text-white">HireMate</span>
                    </div>

                    {/* Welcome Text */}
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">Welcome back!</h2>
                        <p className="text-gray-600 dark:text-gray-400">Sign in to continue to your dashboard</p>
                    </div>

                    {/* Login Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* API Error Message */}
                        {apiError && (
                            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400 text-sm animate-fade-in">
                                <div className="flex items-start gap-2">
                                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                    <span>{apiError}</span>
                                </div>
                            </div>
                        )}
                        {/* Email Field */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                Email Address
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className={`w-full pl-12 pr-4 py-3.5 bg-white dark:bg-neutral-900 border ${errors.email ? 'border-red-500' : 'border-gray-200 dark:border-neutral-700'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                    placeholder="Enter your email"
                                />
                            </div>
                            {errors.email && (
                                <p className="mt-1.5 text-sm text-red-500">{errors.email}</p>
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
                                    className={`w-full pl-12 pr-12 py-3.5 bg-white dark:bg-neutral-900 border ${errors.password ? 'border-red-500' : 'border-gray-200 dark:border-neutral-700'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-800 dark:text-white placeholder-gray-400`}
                                    placeholder="Enter your password"
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
                        </div>

                        {/* Remember Me & Forgot Password */}
                        <div className="flex items-center justify-between">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    name="rememberMe"
                                    checked={formData.rememberMe}
                                    onChange={handleChange}
                                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-600 dark:text-gray-400">Remember me</span>
                            </label>
                            <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors">
                                Forgot password?
                            </Link>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed active:scale-95"
                        >
                            {isLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    <span>Signing in...</span>
                                </>
                            ) : (
                                <>
                                    <span>Sign In</span>
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200 dark:border-neutral-700"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black text-gray-500">
                                Or continue with
                            </span>
                        </div>
                    </div>

                    {/* Social Login */}
                    <div className="grid grid-cols-2 gap-4">
                        <button className="flex items-center justify-center gap-2 py-3 px-4 bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl hover:bg-gray-50 dark:hover:bg-neutral-800 transition-all duration-200 text-gray-700 dark:text-gray-200 font-medium">
                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                            </svg>
                            <span>Google</span>
                        </button>
                        <button className="flex items-center justify-center gap-2 py-3 px-4 bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl hover:bg-gray-50 dark:hover:bg-neutral-800 transition-all duration-200 text-gray-700 dark:text-gray-200 font-medium">
                            <svg className="w-5 h-5" fill="#1877F2" viewBox="0 0 24 24">
                                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                            </svg>
                            <span>Facebook</span>
                        </button>
                    </div>

                    {/* Sign Up Link */}
                    <p className="text-center mt-8 text-gray-600 dark:text-gray-400">
                        Don't have an account?{' '}
                        <Link to="/register" className="text-blue-600 hover:text-blue-700 font-semibold transition-colors">
                            Create account
                        </Link>
                    </p>

                    {/* Security Badge */}
                    <div className="flex items-center justify-center gap-2 mt-8 text-gray-400">
                        <Shield className="w-4 h-4" />
                        <span className="text-xs">Secured with 256-bit SSL encryption</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
