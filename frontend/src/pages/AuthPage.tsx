import { useState } from 'react';
import { ChefHat, Lock, User as UserIcon } from 'lucide-react';
import { login, register } from '../services/api';
import { useAuthStore } from '../stores/auth-store';

export default function AuthPage({ onLoginSuccess }: { onLoginSuccess: () => void }) {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const { setAuth } = useAuthStore();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (!username || !password) {
            setError('请填写用户名和密码');
            return;
        }
        
        setLoading(true);
        try {
            if (isLogin) {
                const res = await login(username, password);
                if (res.access_token) {
                    // 解码 jwt 简单获取信息（这里直接用存储名或请求后端 /me 获取）
                    setAuth(res.access_token, { username, role: 'user' });
                    onLoginSuccess();
                } else {
                    setError('用户名或密码错误');
                }
            } else {
                await register(username, password);
                // 注册成功自动登录
                const res = await login(username, password);
                if (res.access_token) {
                    setAuth(res.access_token, { username, role: 'user' });
                    onLoginSuccess();
                }
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || '请求失败，请检查网络');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-surface flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-50 to-surface">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-6 transition-all duration-300">
                        <ChefHat size={32} className="text-white" />
                    </div>
                </div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-text-primary">
                    走云智能排菜系统
                </h2>
                <p className="mt-2 text-center text-sm text-text-muted">
                    {isLogin ? '欢迎回来，请登录您的账号' : '立即注册，开启智能排餐之旅'}
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-2xl sm:px-10 border border-border-light relative overflow-hidden">
                    <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-primary-400 to-accent-400" />
                    
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {error && (
                            <div className="p-3 bg-red-50 text-red-600 border border-red-100 rounded-xl text-sm animate-fade-in text-center">
                                {error}
                            </div>
                        )}
                        <div>
                            <label className="block text-sm font-medium text-text-secondary">
                                用户名
                            </label>
                            <div className="mt-1 relative rounded-xl shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <UserIcon className="h-5 w-5 text-text-muted" aria-hidden="true" />
                                </div>
                                <input
                                    type="text"
                                    required
                                    className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-border-light rounded-xl py-3 px-4 bg-gray-50/50 hover:bg-white transition-colors outline-none border"
                                    placeholder="输入您的账号"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-text-secondary">
                                密码
                            </label>
                            <div className="mt-1 relative rounded-xl shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-text-muted" aria-hidden="true" />
                                </div>
                                <input
                                    type="password"
                                    required
                                    className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-border-light rounded-xl py-3 px-4 bg-gray-50/50 hover:bg-white transition-colors outline-none border"
                                    placeholder="输入您的密码 (不少于6位)"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
                            >
                                {loading ? '处理中...' : (isLogin ? '立即登录' : '注册并登录')}
                            </button>
                        </div>
                    </form>

                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-border-light" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-white text-text-muted">
                                    {isLogin ? '还没有账号？' : '已有账号？'}
                                </span>
                            </div>
                        </div>

                        <div className="mt-6">
                            <button
                                onClick={() => {
                                    setIsLogin(!isLogin);
                                    setError('');
                                }}
                                className="w-full flex justify-center py-2.5 px-4 border border-border-light rounded-xl shadow-sm text-sm font-medium text-text-secondary bg-white hover:bg-gray-50 transition-colors"
                            >
                                {isLogin ? '注册新账号' : '返回登录'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
