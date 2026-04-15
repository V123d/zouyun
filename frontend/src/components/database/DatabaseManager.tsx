import { useState } from 'react';
import { X, UtensilsCrossed, ClipboardCheck } from 'lucide-react';
import DishLibraryManager from './DishLibraryManager';
import StandardQuotaManager from './StandardQuotaManager';

interface DatabaseManagerProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function DatabaseManager({ isOpen, onClose }: DatabaseManagerProps) {
    const [activeView, setActiveView] = useState<'dishes' | 'standards'>('dishes');

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-md animate-in fade-in duration-300">
            <div className="w-[95vw] h-[90vh] bg-surface rounded-3xl shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 slide-in-from-bottom-4 duration-300">
                {/* Header */}
                <header className="h-16 bg-white border-b border-border-light flex items-center px-6 shrink-0 justify-between">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-2">
                            <div className="w-9 h-9 rounded-xl bg-primary-600 flex items-center justify-center text-white shadow-lg shadow-primary-200">
                                <UtensilsCrossed size={20} />
                            </div>
                            <h2 className="text-lg font-bold text-text-primary tracking-tight">后台数据中心</h2>
                        </div>
                        
                        <nav className="flex items-center gap-1 bg-gray-100 p-1 rounded-xl">
                            <button
                                onClick={() => setActiveView('dishes')}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                                    activeView === 'dishes' 
                                        ? 'bg-white text-primary-600 shadow-sm' 
                                        : 'text-text-muted hover:text-text-secondary'
                                }`}
                            >
                                <UtensilsCrossed size={16} />
                                菜品库管理
                            </button>
                            <button
                                onClick={() => setActiveView('standards')}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                                    activeView === 'standards' 
                                        ? 'bg-white text-primary-600 shadow-sm' 
                                        : 'text-text-muted hover:text-text-secondary'
                                }`}
                            >
                                <ClipboardCheck size={16} />
                                营养标准配置
                            </button>
                        </nav>
                    </div>

                    <button 
                        onClick={onClose}
                        className="w-10 h-10 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors border border-transparent hover:border-border"
                    >
                        <X size={20} className="text-text-muted" />
                    </button>
                </header>

                {/* Content */}
                <main className="flex-1 overflow-hidden relative">
                    {activeView === 'dishes' ? (
                        <DishLibraryManager />
                    ) : (
                        <StandardQuotaManager />
                    )}
                </main>

                {/* Footer / Status */}
                <footer className="h-10 bg-white border-t border-border-light px-6 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-4 text-[11px] text-text-muted">
                        <div className="flex items-center gap-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                            数据库连接正常
                        </div>
                        <span className="opacity-30">|</span>
                        <span>系统版本：v2.0.4-stable</span>
                    </div>
                </footer>
            </div>
        </div>
    );
}
