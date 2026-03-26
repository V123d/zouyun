import { useState, useEffect } from 'react';
import { 
    Save, ShieldCheck, AlertCircle, Info, 
    RefreshCw, Hash
} from 'lucide-react';
import { getStandardQuotas, updateStandardQuota } from '../../services/api';
import type { StandardQuota, KitchenClass } from '../../types';

const CATEGORIES = [
    "大米", "面粉", "畜肉", "禽肉", "禽蛋", "鱼虾", "牛奶", 
    "大豆", "蔗糖", "植物油", "蔬菜", "水果", "食用菌(干)", "干菜"
];

export default function StandardQuotaManager() {
    const [quotas, setQuotas] = useState<StandardQuota[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<KitchenClass>('一类灶');
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const data = await getStandardQuotas();
            setQuotas(data);
        } catch (err) {
            setError('获取数据失败');
        } finally {
            setLoading(false);
        }
    };

    const currentQuota = quotas.find((q: StandardQuota) => q.class_type === activeTab);

    const handleUpdateValue = (key: string, value: number) => {
        if (!currentQuota) return;
        const nextQuotas = quotas.map((q: StandardQuota) => {
            if (q.class_type === activeTab) {
                return {
                    ...q,
                    quotas: { ...q.quotas, [key]: value }
                };
            }
            return q;
        });
        setQuotas(nextQuotas);
    };

    const handleSave = async () => {
        if (!currentQuota) return;
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            await updateStandardQuota(currentQuota.id, currentQuota);
            setSuccessMessage(`已保存 ${activeTab} 的准则配置`);
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setError('同步到后端失败');
        } finally {
            setIsSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-text-muted gap-3">
                <RefreshCw className="animate-spin text-primary-500" size={24} />
                <span className="text-sm">正在加载标准数据...</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-surface/30">
            {/* 顶部页签 */}
            <div className="bg-white px-6 pt-4 border-b border-border-light shadow-sm">
                <div className="flex items-center gap-8">
                    {(['一类灶', '二类灶', '三类灶'] as KitchenClass[]).map((type: KitchenClass) => (
                        <button
                            key={type}
                            onClick={() => setActiveTab(type)}
                            className={`pb-3 text-sm font-bold transition-all relative ${
                                activeTab === type 
                                    ? 'text-primary-600' 
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            {type}
                            {activeTab === type && (
                                <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary-500 rounded-t-full" />
                            )}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* 提示栏 */}
                    {error && (
                        <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl flex items-center gap-2 text-sm animate-shake">
                            <AlertCircle size={18} />
                            {error}
                        </div>
                    )}
                    {successMessage && (
                        <div className="bg-green-50 border border-green-100 text-green-600 px-4 py-3 rounded-xl flex items-center gap-2 text-sm animate-in slide-in-from-top-2">
                            <ShieldCheck size={18} />
                            {successMessage}
                        </div>
                    )}

                    {!currentQuota ? (
                        <div className="p-12 text-center border-2 border-dashed border-border rounded-2xl">
                            <p className="text-text-muted mb-4">尚未配置 {activeTab} 的定量标准</p>
                            <button className="px-6 py-2 bg-primary-600 text-white rounded-xl text-sm font-bold">
                                立即初始化
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {CATEGORIES.map((cat: string) => (
                                <div key={cat} className="bg-white p-4 rounded-2xl border border-border-light shadow-sm hover:shadow-md transition-shadow group">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-primary-50 transition-colors">
                                                <Hash size={14} className="text-text-muted group-hover:text-primary-500" />
                                            </div>
                                            <span className="text-sm font-bold text-text-primary">{cat}</span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <input
                                                type="number"
                                                min={0}
                                                step={0.1}
                                                value={currentQuota.quotas[cat] ?? 0}
                                                onChange={(e) => handleUpdateValue(cat, Number(e.target.value))}
                                                className="w-24 px-3 py-1.5 bg-surface border border-border rounded-lg text-sm text-right font-mono focus:border-primary-400 outline-none transition-all"
                                            />
                                            <span className="text-xs text-text-muted font-medium w-8">g/日</span>
                                        </div>
                                    </div>
                                    <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                                        <div 
                                            className="h-full bg-primary-400 opacity-60 transition-all duration-500" 
                                            style={{ width: `${Math.min(100, (currentQuota.quotas[cat] || 0) / 5)}%` }} 
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* 说明卡片 */}
                    <div className="bg-primary-50/50 border border-primary-100 rounded-2xl p-5 flex gap-4">
                        <Info className="text-primary-500 shrink-0 mt-0.5" size={20} />
                        <div>
                            <h4 className="text-sm font-bold text-primary-900 mb-1">指标说明</h4>
                            <ul className="text-xs text-primary-800/70 space-y-1.5 leading-relaxed">
                                <li>• 此标准用于“约束校验智能体”计算每日摄入达标度。</li>
                                <li>• 修改标准后，系统将自动对现有的排菜方案进行重新评估。</li>
                                <li>• 定量数值应参考《伙食费标准及食物定量标准》最新规定。</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* 底部保存条 */}
            <div className="bg-white border-t border-border-light p-4 px-6 flex items-center justify-between">
                <div className="text-xs text-text-muted flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    云端数据已同步至：{new Date().toLocaleTimeString()}
                </div>
                <button
                    onClick={handleSave}
                    disabled={isSaving || !currentQuota}
                    className="flex items-center gap-2 px-8 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-primary-200 hover:bg-primary-700 active:scale-95 transition-all disabled:opacity-50"
                >
                    {isSaving ? <RefreshCw className="animate-spin" size={16} /> : <Save size={16} />}
                    {isSaving ? '正在同步...' : `保存并应用到 ${activeTab}`}
                </button>
            </div>
        </div>
    );
}
