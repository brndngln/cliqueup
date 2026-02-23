import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Calendar } from '../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { format } from 'date-fns';
import { CalendarIcon, Eye, EyeOff, Sparkles, Users, Heart, MessageCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { toast } from 'sonner';

export default function LandingPage() {
    const { user } = useAuth();
    const navigate = useNavigate();

    if (user) {
        navigate('/home');
        return null;
    }

    return (
        <div className="min-h-screen bg-background relative overflow-hidden">
            {/* Background effects */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-indigo-500/10 via-transparent to-transparent rounded-full blur-3xl" />
                <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-pink-500/10 via-transparent to-transparent rounded-full blur-3xl" />
            </div>

            {/* Header */}
            <header className="relative z-10 flex items-center justify-between px-6 py-4 lg:px-12">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-pink-500 flex items-center justify-center">
                        <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-heading text-2xl font-bold">NEXUS</span>
                </div>
                <div className="flex items-center gap-4">
                    <Link to="/login">
                        <Button variant="ghost" className="rounded-full" data-testid="login-nav-btn">
                            Log in
                        </Button>
                    </Link>
                    <Link to="/signup">
                        <Button className="rounded-full bg-primary hover:bg-primary/90" data-testid="signup-nav-btn">
                            Get Started
                        </Button>
                    </Link>
                </div>
            </header>

            {/* Hero Section */}
            <main className="relative z-10 max-w-7xl mx-auto px-6 lg:px-12 pt-16 lg:pt-24">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Left content */}
                    <div className="space-y-8">
                        <div className="space-y-4">
                            <span className="inline-block px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium">
                                Social + Dating, Unified
                            </span>
                            <h1 className="font-heading text-5xl md:text-7xl font-bold tracking-tight leading-none">
                                Connect with your
                                <span className="text-gradient-social"> Squad</span>
                            </h1>
                            <p className="text-lg md:text-xl text-muted-foreground max-w-lg leading-relaxed">
                                The first platform where social meets dating. Build your squad, share your story, and discover connections that matter.
                            </p>
                        </div>

                        <div className="flex flex-wrap gap-4">
                            <Link to="/signup">
                                <Button size="lg" className="rounded-full h-12 px-8 bg-primary hover:bg-primary/90 font-semibold tap-feedback" data-testid="hero-get-started-btn">
                                    Get Started Free
                                </Button>
                            </Link>
                            <Button size="lg" variant="outline" className="rounded-full h-12 px-8 font-semibold" data-testid="learn-more-btn">
                                Learn More
                            </Button>
                        </div>

                        {/* Stats */}
                        <div className="flex gap-8 pt-4">
                            <div>
                                <p className="font-heading text-3xl font-bold">1M+</p>
                                <p className="text-sm text-muted-foreground">Active Users</p>
                            </div>
                            <div>
                                <p className="font-heading text-3xl font-bold">500K+</p>
                                <p className="text-sm text-muted-foreground">Squads Formed</p>
                            </div>
                            <div>
                                <p className="font-heading text-3xl font-bold">100K+</p>
                                <p className="text-sm text-muted-foreground">Matches Made</p>
                            </div>
                        </div>
                    </div>

                    {/* Right content - Feature cards */}
                    <div className="relative">
                        <div className="grid grid-cols-2 gap-4">
                            {/* Feature Card 1 */}
                            <div className="glass-card p-6 space-y-4 hover-lift">
                                <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                                    <Users className="w-6 h-6 text-indigo-400" />
                                </div>
                                <h3 className="font-heading text-lg font-semibold">Squad Dating</h3>
                                <p className="text-sm text-muted-foreground">Match with other squads for group adventures and double dates.</p>
                            </div>

                            {/* Feature Card 2 */}
                            <div className="glass-card p-6 space-y-4 hover-lift mt-8">
                                <div className="w-12 h-12 rounded-xl bg-pink-500/20 flex items-center justify-center">
                                    <Heart className="w-6 h-6 text-pink-400" />
                                </div>
                                <h3 className="font-heading text-lg font-semibold">Meaningful Matches</h3>
                                <p className="text-sm text-muted-foreground">Your squad votes together. No more awkward solo swiping.</p>
                            </div>

                            {/* Feature Card 3 */}
                            <div className="glass-card p-6 space-y-4 hover-lift">
                                <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                                    <MessageCircle className="w-6 h-6 text-purple-400" />
                                </div>
                                <h3 className="font-heading text-lg font-semibold">Social First</h3>
                                <p className="text-sm text-muted-foreground">Share posts, stories, and videos with your network.</p>
                            </div>

                            {/* Feature Card 4 */}
                            <div className="glass-card p-6 space-y-4 hover-lift mt-8">
                                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                                    <Sparkles className="w-6 h-6 text-emerald-400" />
                                </div>
                                <h3 className="font-heading text-lg font-semibold">Safe & Verified</h3>
                                <p className="text-sm text-muted-foreground">Age verification and photo checks keep everyone safe.</p>
                            </div>
                        </div>

                        {/* Floating avatars */}
                        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2">
                            <div className="avatar-stack flex">
                                <img src="https://images.unsplash.com/photo-1618698937393-8d7bb5f2d341?w=100&h=100&fit=crop" alt="User" className="w-10 h-10 rounded-full object-cover" />
                                <img src="https://images.unsplash.com/photo-1733069523650-21e13fa4daeb?w=100&h=100&fit=crop" alt="User" className="w-10 h-10 rounded-full object-cover" />
                                <img src="https://images.unsplash.com/photo-1710182240446-8ae8c223e135?w=100&h=100&fit=crop" alt="User" className="w-10 h-10 rounded-full object-cover" />
                                <div className="w-10 h-10 rounded-full bg-zinc-800 border-2 border-background flex items-center justify-center text-xs font-medium">+99</div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="relative z-10 mt-24 py-8 border-t border-border/50">
                <div className="max-w-7xl mx-auto px-6 lg:px-12 flex flex-wrap items-center justify-between gap-4">
                    <p className="text-sm text-muted-foreground">© 2026 NEXUS. All rights reserved.</p>
                    <div className="flex gap-6">
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacy</a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Terms</a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Contact</a>
                    </div>
                </div>
            </footer>
        </div>
    );
}
