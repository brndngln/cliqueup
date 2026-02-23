import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Calendar } from '../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { format, subYears, isAfter } from 'date-fns';
import { CalendarIcon, Eye, EyeOff, Sparkles, ArrowLeft, Check, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { toast } from 'sonner';

export default function SignupPage() {
    const [step, setStep] = useState(1);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [handle, setHandle] = useState('');
    const [dob, setDob] = useState(null);
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const { signup } = useAuth();
    const navigate = useNavigate();

    const maxDate = subYears(new Date(), 13); // Must be at least 13
    const isAdult = dob && isAfter(subYears(new Date(), 18), dob);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (step === 1) {
            if (!dob) {
                toast.error('Please select your date of birth');
                return;
            }
            setStep(2);
            return;
        }

        setLoading(true);
        try {
            const formattedDob = format(dob, 'yyyy-MM-dd');
            await signup({
                email,
                password,
                display_name: displayName,
                handle: handle.toLowerCase(),
                dob: formattedDob,
            });
            toast.success('Welcome to CliqUp!');
            navigate('/home');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Signup failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex">
            {/* Left side - Image */}
            <div className="hidden lg:block flex-1 relative">
                <div className="absolute inset-0 bg-gradient-to-br from-pink-500/20 via-gray-500/10 to-teal-500/20" />
                <img
                    src="https://images.unsplash.com/photo-1616189221633-c3e3acb720af?w=1200&h=1600&fit=crop"
                    alt="Friends"
                    className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
                <div className="absolute bottom-12 left-12 right-12 glass-card p-6">
                    <p className="text-lg font-medium mb-2">"Join with your friends, match with squads"</p>
                    <p className="text-sm text-muted-foreground">— The future of dating is social</p>
                </div>
            </div>

            {/* Right side - Form */}
            <div className="flex-1 flex flex-col justify-center px-6 lg:px-12 py-12">
                <div className="max-w-md mx-auto w-full">
                    <Link to="/" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-8 transition-colors">
                        <ArrowLeft className="w-4 h-4" />
                        Back to home
                    </Link>

                    <div className="flex items-center gap-2 mb-8">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-teal-500 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-heading text-2xl font-bold">CliqUp</span>
                    </div>

                    {/* Progress indicator */}
                    <div className="flex gap-2 mb-8">
                        <div className={cn("h-1 flex-1 rounded-full", step >= 1 ? "bg-primary" : "bg-muted")} />
                        <div className={cn("h-1 flex-1 rounded-full", step >= 2 ? "bg-primary" : "bg-muted")} />
                    </div>

                    <div className="space-y-2 mb-8">
                        <h1 className="font-heading text-3xl font-bold">
                            {step === 1 ? "Let's get started" : "Create your account"}
                        </h1>
                        <p className="text-muted-foreground">
                            {step === 1 ? "First, tell us your birthday" : "Almost there! Set up your profile"}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {step === 1 ? (
                            <>
                                <div className="space-y-2">
                                    <Label>Date of Birth</Label>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <Button
                                                variant="outline"
                                                className={cn(
                                                    "w-full h-12 justify-start text-left font-normal",
                                                    !dob && "text-muted-foreground"
                                                )}
                                                data-testid="dob-picker-btn"
                                            >
                                                <CalendarIcon className="mr-2 h-4 w-4" />
                                                {dob ? format(dob, "MMMM d, yyyy") : "Pick your birthday"}
                                            </Button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0" align="start">
                                            <Calendar
                                                mode="single"
                                                selected={dob}
                                                onSelect={setDob}
                                                disabled={(date) => date > maxDate || date < new Date("1920-01-01")}
                                                initialFocus
                                                captionLayout="dropdown-buttons"
                                                fromYear={1920}
                                                toYear={new Date().getFullYear() - 13}
                                            />
                                        </PopoverContent>
                                    </Popover>
                                    {dob && (
                                        <div className={cn(
                                            "flex items-center gap-2 text-sm p-3 rounded-lg",
                                            isAdult ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
                                        )}>
                                            {isAdult ? (
                                                <>
                                                    <Check className="w-4 h-4" />
                                                    <span>You'll have access to all features including Meet (dating)</span>
                                                </>
                                            ) : (
                                                <>
                                                    <AlertCircle className="w-4 h-4" />
                                                    <span>You'll have access to social features. Dating requires 18+</span>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="displayName">Display Name</Label>
                                    <Input
                                        id="displayName"
                                        placeholder="Your name"
                                        value={displayName}
                                        onChange={(e) => setDisplayName(e.target.value)}
                                        required
                                        className="h-12"
                                        data-testid="signup-name-input"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="handle">Username</Label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">@</span>
                                        <Input
                                            id="handle"
                                            placeholder="username"
                                            value={handle}
                                            onChange={(e) => setHandle(e.target.value.replace(/[^a-zA-Z0-9_]/g, ''))}
                                            required
                                            className="h-12 pl-8"
                                            data-testid="signup-handle-input"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="h-12"
                                        data-testid="signup-email-input"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="password">Password</Label>
                                    <div className="relative">
                                        <Input
                                            id="password"
                                            type={showPassword ? 'text' : 'password'}
                                            placeholder="At least 8 characters"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                            minLength={8}
                                            className="h-12 pr-10"
                                            data-testid="signup-password-input"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                        >
                                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}

                        <div className="flex gap-3">
                            {step === 2 && (
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="flex-1 h-12 rounded-full"
                                    onClick={() => setStep(1)}
                                >
                                    Back
                                </Button>
                            )}
                            <Button
                                type="submit"
                                className="flex-1 h-12 rounded-full bg-primary hover:bg-primary/90 font-semibold tap-feedback"
                                disabled={loading || (step === 1 && !dob)}
                                data-testid="signup-submit-btn"
                            >
                                {loading ? 'Creating account...' : step === 1 ? 'Continue' : 'Create Account'}
                            </Button>
                        </div>
                    </form>

                    <p className="text-center text-sm text-muted-foreground mt-6">
                        Already have an account?{' '}
                        <Link to="/login" className="text-primary hover:underline font-medium">
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
