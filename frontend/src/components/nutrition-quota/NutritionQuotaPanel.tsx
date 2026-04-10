/* ========== 每日营养配额达标详情面板 ========== */
import { useState } from 'react';
import {
    X,
    Apple,
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronDown,
    Calendar,
} from 'lucide-react';
import { useAppStore } from '../../stores/app-store';
import type { QuotaCompliance } from '../../types';

interface NutritionQuotaPanelProps {
    onClose: () => void;
}

const CATEGORY_ICONS: Record<string, string> = {
    '大米': '🍚',
    '面粉': '🌾',
    '畜肉': '🥩',
    '禽肉': '🍗',
    '禽蛋': '🥚',
    '鱼虾': '🐟',
    '牛奶': '🥛',
    '大豆': '🫘',
    '蔗糖': '🍬',
    '植物油': '🫒',
    '鲜蔬菜': '🥬',
    '水果': '🍎',
    '食用菌(干)': '🍄',
    '干菜': '🥗',
};

const NUTRITION_ICONS: Record<string, string> = {
    '卡路里': '🔥',
    '蛋白质': '💪',
    '脂肪': '🧈',
    '碳水化合物': '🍞',
};

// const NUTRITION_UNITS: Record<string, string> = {
//     '卡路里': 'kcal',
//     '蛋白质': 'g',
//     '脂肪': 'g',
//     '碳水化合物': 'g',
// };

function getRateColor(rate: number): string {
    if (rate >= 0.9) return 'text-green-600';
    if (rate >= 0.5) return 'text-amber-600';
    return 'text-red-500';
}

function getRateBgColor(rate: number): string {
    if (rate >= 0.9) return 'bg-green-100 border-green-200';
    if (rate >= 0.5) return 'bg-amber-100 border-amber-200';
    return 'bg-red-100 border-red-200';
}

function getRateLabel(rate: number): string {
    if (rate >= 0.9) return '达标良好';
    if (rate >= 0.5) return '偏低';
    return '严重不足';
}

function RateBar({ rate }: { rate: number }) {
    const colorClass = getRateBgColor(rate);
    const pct = Math.min(rate * 100, 100);
    return (
        <div className={`w-16 h-2 rounded-full overflow-hidden border ${colorClass} bg-gray-100`}>
            <div
                className={`h-full rounded-full transition-all duration-500 ${
                    rate >= 0.9 ? 'bg-green-400' : rate >= 0.5 ? 'bg-amber-400' : 'bg-red-400'
                }`}
                style={{ width: `${pct}%` }}
            />
        </div>
    );
}

function NutrientCard({ q }: { q: QuotaCompliance }) {
    const unit = q.unit || 'g';
    const icon = NUTRITION_ICONS[q.name] || '📊';

    return (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getRateBgColor(q.rate)}`}>
            <span className="text-base w-6 text-center shrink-0">{icon}</span>
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-medium text-text-primary truncate">{q.name}</span>
                    <span className={`text-[10px] font-semibold ml-2 ${getRateColor(q.rate)}`}>
                        {getRateLabel(q.rate)}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <RateBar rate={q.rate} />
                    <div className="flex items-center gap-1 text-[10px] text-text-muted">
                        <span>{q.actual}{unit}</span>
                        <span>/</span>
                        <span>{q.standard}{unit}</span>
                        <span className="font-medium text-text-secondary">
                            ({Math.round(q.rate * 100)}%)
                        </span>
                    </div>
                </div>
            </div>
            <div className="shrink-0">
                {q.rate >= 0.9 ? (
                    <TrendingUp size={12} className="text-green-500" />
                ) : q.rate >= 0.5 ? (
                    <Minus size={12} className="text-amber-500" />
                ) : (
                    <TrendingDown size={12} className="text-red-500" />
                )}
            </div>
        </div>
    );
}

function IngredientCard({ q }: { q: QuotaCompliance }) {
    return (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getRateBgColor(q.rate)}`}>
            <span className="text-base w-6 text-center shrink-0">
                {CATEGORY_ICONS[q.name] || '📦'}
            </span>
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-medium text-text-primary truncate">{q.name}</span>
                    <span className={`text-[10px] font-semibold ml-2 ${getRateColor(q.rate)}`}>
                        {getRateLabel(q.rate)}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <RateBar rate={q.rate} />
                    <div className="flex items-center gap-1 text-[10px] text-text-muted">
                        <span>{q.actual}g</span>
                        <span>/</span>
                        <span>{q.standard}g</span>
                        <span className="font-medium text-text-secondary">
                            ({Math.round(q.rate * 100)}%)
                        </span>
                    </div>
                </div>
            </div>
            <div className="shrink-0">
                {q.rate >= 0.9 ? (
                    <TrendingUp size={12} className="text-green-500" />
                ) : q.rate >= 0.5 ? (
                    <Minus size={12} className="text-amber-500" />
                ) : (
                    <TrendingDown size={12} className="text-red-500" />
                )}
            </div>
        </div>
    );
}

function SingleDayCard({ date, compliance }: { date: string; compliance: QuotaCompliance[] }) {
    const [expanded, setExpanded] = useState(false);
    const currentQuotaType = useAppStore(s => (s as any).currentQuotaType || 'ingredient');

    const dateLabel = (() => {
        try {
            const d = new Date(date + 'T00:00:00');
            const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
            return `${d.getMonth() + 1}/${d.getDate()} ${weekdays[d.getDay()]}`;
        } catch {
            return date;
        }
    })();

    const deficitCount = compliance.filter(q => q.rate < 0.5).length;
    const goodCount = compliance.filter(q => q.rate >= 0.9).length;
    const totalCount = compliance.length;

    return (
        <div className="border border-border rounded-xl overflow-hidden bg-white hover:shadow-md transition-shadow">
            {/* 日期标题行 */}
            <button
                className="w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r from-surface to-white hover:from-primary-50/50 transition-colors"
                onClick={() => setExpanded(v => !v)}
            >
                <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-text-muted" />
                    <span className="text-sm font-semibold text-text-primary">{dateLabel}</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-green-600 font-medium">{goodCount} 达标</span>
                        <span className="text-text-muted">/</span>
                        <span className="text-red-500 font-medium">{deficitCount} 不足</span>
                    </div>
                    <span className="text-[10px] text-text-muted bg-surface px-2 py-0.5 rounded-full">
                        {totalCount} 项
                    </span>
                    <ChevronDown size={14} className={`text-text-muted transition-transform ${expanded ? 'rotate-180' : ''}`} />
                </div>
            </button>

            {/* 明细展开区 */}
            {expanded && (
                <div className="px-4 pb-3 space-y-1.5">
                    {compliance.map((q, i) => (
                        currentQuotaType === 'nutrition' ? (
                            <NutrientCard key={i} q={q} />
                        ) : (
                            <IngredientCard key={i} q={q} />
                        )
                    ))}
                </div>
            )}
        </div>
    );
}

export default function NutritionQuotaPanel({ onClose }: NutritionQuotaPanelProps) {
    const { dailyQuotaCompliance } = useAppStore();

    const dates = Object.keys(dailyQuotaCompliance).sort();

    // 全局汇总统计
    const allCompliance = Object.values(dailyQuotaCompliance).flat();
    const overallGood = allCompliance.filter(q => q.rate >= 0.9).length;
    const overallDeficit = allCompliance.filter(q => q.rate < 0.5).length;
    const overallTotal = allCompliance.length;

    return (
        <>
            {/* 遮罩 */}
            <div
                className="fixed inset-0 bg-black/20 z-40 backdrop-blur-sm animate-fade-in"
                onClick={onClose}
            />

            {/* 面板 */}
            <div
                className="fixed left-0 top-0 h-full w-[420px] max-w-[95vw] bg-white z-50 shadow-2xl animate-slide-right overflow-hidden flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* 头部 */}
                <div
                    className="px-5 py-4 border-b border-border-light flex items-center justify-between bg-gradient-to-r from-primary-50 to-accent-50"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div>
                        <h2 className="text-base font-bold text-text-primary">每日营养配额达标详情</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 rounded-lg hover:bg-white/60 flex items-center justify-center"
                    >
                        <X size={16} className="text-text-secondary" />
                    </button>
                </div>

                {/* 汇总条 */}
                {overallTotal > 0 && (
                    <div className="px-5 py-3 bg-surface border-b border-border-light flex items-center gap-4">
                        <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-green-500" />
                            <span className="text-xs text-text-secondary">
                                达标 <span className="font-bold text-green-600">{overallGood}</span> 项
                            </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-red-500" />
                            <span className="text-xs text-text-secondary">
                                不足 <span className="font-bold text-red-500">{overallDeficit}</span> 项
                            </span>
                        </div>
                        <div className="ml-auto flex items-center gap-1 text-[10px] text-text-muted">
                            <Apple size={10} />
                            共 {overallTotal} 项 / {dates.length} 天
                        </div>
                    </div>
                )}

                {/* 内容 */}
                <div
                    className="flex-1 overflow-y-auto p-4 space-y-3"
                    onClick={(e) => e.stopPropagation()}
                >
                    {dates.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-text-muted gap-3">
                            <Apple size={40} className="opacity-30" />
                            <p className="text-sm">暂无营养达标数据</p>
                            <p className="text-xs text-text-muted/60">请先生成菜单，系统将自动计算每日营养配额达标情况</p>
                        </div>
                    ) : (
                        <>
                            {dates.map((date) => (
                                <SingleDayCard
                                    key={date}
                                    date={date}
                                    compliance={dailyQuotaCompliance[date]}
                                />
                            ))}
                        </>
                    )}
                </div>

                {/* 底部说明 */}
                {dates.length > 0 && (
                    <div className="px-5 py-3 border-t border-border-light bg-surface">
                        <p className="text-[10px] text-text-muted leading-relaxed">
                            营养配额达标率仅供参考，系统仅在提示词中建议 LLM 尽可能满足。
                            达标率 &lt; 50% 视为严重不足，建议在配置中调整食材选择。
                        </p>
                    </div>
                )}
            </div>
        </>
    );
}
