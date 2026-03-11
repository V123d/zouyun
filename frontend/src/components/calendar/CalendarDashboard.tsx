/* ========== 周菜单日历看板 (Calendar Dashboard) ========== */
import { useState } from 'react';
import {
    DollarSign,
    Heart,
    RefreshCw,
    AlertTriangle,
    Plus,
    Eye,
    FileText,
    Search,
    X,
} from 'lucide-react';
import { useAppStore } from '../../stores/app-store';
import { getDateRange, getWeekdayLabel, formatDateShort } from '../../utils/date';
import { showNotImplemented, searchDishes } from '../../services/api';
import type { DishInfo } from '../../types';

export default function CalendarDashboard() {
    const { config, weeklyMenu, metrics, setWeeklyMenu } = useAppStore();
    const enabledMeals = config.meals_config.filter((m) => m.enabled);
    const dates = getDateRange(
        config.context_overview.schedule.start_date,
        config.context_overview.schedule.end_date
    );

    const [searchOpen, setSearchOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<DishInfo[]>([]);
    const [searchTarget, setSearchTarget] = useState<{
        date: string;
        meal: string;
        category: string;
    } | null>(null);

    const handleSearch = async (query: string) => {
        setSearchQuery(query);
        if (query.length >= 1) {
            const results = await searchDishes(query);
            setSearchResults(results);
        } else {
            setSearchResults([]);
        }
    };

    const handleAddDish = (dish: DishInfo) => {
        if (!searchTarget || !weeklyMenu) return;
        const { date, meal, category } = searchTarget;
        const updated = { ...weeklyMenu };
        if (!updated[date]) updated[date] = {};
        if (!updated[date][meal]) updated[date][meal] = {};
        if (!updated[date][meal][category]) updated[date][meal][category] = [];
        updated[date][meal][category] = [
            ...updated[date][meal][category],
            { ...dish, is_manual_added: true },
        ];
        setWeeklyMenu(updated);
        setSearchOpen(false);
    };

    const openSearch = (date: string, meal: string, category: string) => {
        setSearchTarget({ date, meal, category });
        setSearchQuery('');
        setSearchResults([]);
        setSearchOpen(true);
    };

    /** 获取某个单元格中的菜品 */
    const getCellDishes = (date: string, mealName: string, categoryName: string): DishInfo[] => {
        if (!weeklyMenu) return [];
        return weeklyMenu[date]?.[mealName]?.[categoryName] || [];
    };

    return (
        <div className="flex flex-col h-full bg-surface">
            {/* 顶部栏 */}
            <div className="px-5 py-3 bg-white border-b border-border-light flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <h2 className="text-sm font-bold text-text-primary">周菜单看板</h2>
                    <span className="text-xs text-text-muted">
                        {config.context_overview.schedule.start_date.slice(5)} ~ {config.context_overview.schedule.end_date.slice(5)}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => showNotImplemented('预览完整菜单')}
                        className="px-3 py-1.5 text-xs font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors flex items-center gap-1"
                    >
                        <Eye size={12} /> 预览完整菜单
                    </button>
                    <button
                        onClick={() => showNotImplemented('营养报告')}
                        className="px-3 py-1.5 text-xs font-medium text-accent-600 bg-accent-50 rounded-lg hover:bg-accent-100 transition-colors flex items-center gap-1"
                    >
                        <FileText size={12} /> 营养报告
                    </button>
                </div>
            </div>

            {/* 核心指标仪表盘 */}
            <div className="px-5 py-3 grid grid-cols-4 gap-3">
                <MetricCard
                    icon={<DollarSign size={16} />}
                    label="预计总成本"
                    value={metrics ? `¥${metrics.total_cost.toLocaleString()}` : '—'}
                    color="primary"
                />
                <MetricCard
                    icon={<Heart size={16} />}
                    label="营养达标率"
                    value={metrics ? `${metrics.avg_nutrition_score}%` : '—'}
                    color="accent"
                />
                <MetricCard
                    icon={<RefreshCw size={16} />}
                    label="菜品重复率"
                    value={metrics ? `${metrics.repeat_rate}%` : '—'}
                    color="warm"
                />
                <MetricCard
                    icon={<AlertTriangle size={16} />}
                    label="约束告警"
                    value={metrics ? `${metrics.alert_count}项` : '—'}
                    color="red"
                />
            </div>

            {/* 日历网格 */}
            <div className="flex-1 px-5 pb-4 overflow-auto">
                <div className="bg-white rounded-xl border border-border-light shadow-sm overflow-hidden">
                    <table className="w-full border-collapse text-xs">
                        <thead>
                            <tr className="bg-gradient-to-r from-primary-50 to-accent-50">
                                <th className="px-3 py-2.5 text-left font-semibold text-text-secondary border-b border-r border-border-light w-16">
                                    餐次
                                </th>
                                <th className="px-3 py-2.5 text-left font-semibold text-text-secondary border-b border-r border-border-light w-16">
                                    分类
                                </th>
                                {dates.map((d) => (
                                    <th
                                        key={d}
                                        className="px-2 py-2.5 text-center font-semibold text-text-secondary border-b border-r border-border-light last:border-r-0 min-w-[100px]"
                                    >
                                        <div>{getWeekdayLabel(d)}</div>
                                        <div className="text-[10px] text-text-muted font-normal mt-0.5">{formatDateShort(d)}</div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {enabledMeals.map((meal) =>
                                meal.dish_structure.categories.map((cat, catIdx) => (
                                    <tr
                                        key={`${meal.id}-${catIdx}`}
                                        className="hover:bg-gray-50/50 transition-colors"
                                    >
                                        {/* 餐次名称（合并行） */}
                                        {catIdx === 0 && (
                                            <td
                                                rowSpan={meal.dish_structure.categories.length}
                                                className="px-3 py-2 font-semibold text-text-primary border-b border-r border-border-light bg-gray-50/30 align-top text-center"
                                            >
                                                <span className="writing-mode-vertical inline-block">{meal.meal_name}</span>
                                            </td>
                                        )}
                                        {/* 分类名称 */}
                                        <td className="px-3 py-2 text-text-secondary border-b border-r border-border-light bg-gray-50/10 whitespace-nowrap">
                                            {cat.name}
                                        </td>
                                        {/* 日期单元格 */}
                                        {dates.map((d) => {
                                            const dishes = getCellDishes(d, meal.meal_name, cat.name);
                                            return (
                                                <td
                                                    key={d}
                                                    className="px-1.5 py-1.5 border-b border-r border-border-light last:border-r-0 align-top group min-h-[48px] relative"
                                                >
                                                    {dishes.length > 0 ? (
                                                        <div className="space-y-1">
                                                            {dishes.map((dish, i) => (
                                                                <div
                                                                    key={i}
                                                                    className={`px-2 py-1.5 rounded-lg text-[11px] cursor-pointer transition-all hover:shadow-sm ${dish.is_manual_added
                                                                            ? 'bg-warm-50 border border-warm-200 text-warm-700'
                                                                            : 'bg-primary-50/70 border border-primary-100 text-primary-700'
                                                                        }`}
                                                                    onClick={() => showNotImplemented('菜品定量配方')}
                                                                    title={`${dish.name}\n工艺: ${dish.process_type}\n成本: ¥${dish.cost_per_serving}`}
                                                                >
                                                                    <p className="font-medium truncate">{dish.name}</p>
                                                                    <p className="text-[9px] text-text-muted mt-0.5">
                                                                        ¥{dish.cost_per_serving} · {dish.process_type}
                                                                    </p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    ) : (
                                                        <div className="h-10 flex items-center justify-center">
                                                            <span className="text-[10px] text-text-muted">—</span>
                                                        </div>
                                                    )}
                                                    {/* 添加按钮 (hover 显示) */}
                                                    <button
                                                        onClick={() => openSearch(d, meal.meal_name, cat.name)}
                                                        className="absolute bottom-0.5 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity
                              px-2 py-0.5 text-[10px] bg-primary-500 text-white rounded-md flex items-center gap-0.5 hover:bg-primary-600"
                                                    >
                                                        <Plus size={8} /> 添加
                                                    </button>
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 菜品搜索弹窗 */}
            {searchOpen && (
                <>
                    <div
                        className="fixed inset-0 bg-black/20 z-50 backdrop-blur-sm"
                        onClick={() => setSearchOpen(false)}
                    />
                    <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[400px] max-h-[500px] bg-white rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
                        <div className="px-4 py-3 border-b border-border-light flex items-center justify-between">
                            <h3 className="text-sm font-semibold">搜索菜品库</h3>
                            <button onClick={() => setSearchOpen(false)} className="w-6 h-6 rounded hover:bg-gray-100 flex items-center justify-center">
                                <X size={14} />
                            </button>
                        </div>
                        {searchTarget && (
                            <p className="px-4 pt-2 text-[11px] text-text-muted">
                                添加到：{searchTarget.meal} &gt; {searchTarget.category} &gt; {getWeekdayLabel(searchTarget.date)}
                            </p>
                        )}
                        <div className="px-4 py-2">
                            <div className="flex items-center gap-2 border border-border rounded-lg px-3 py-2 focus-within:border-primary-400">
                                <Search size={14} className="text-text-muted" />
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => handleSearch(e.target.value)}
                                    placeholder="输入菜品名称搜索..."
                                    className="flex-1 bg-transparent outline-none text-sm"
                                    autoFocus
                                />
                            </div>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto px-4 pb-4 space-y-1.5">
                            {searchResults.length > 0 ? (
                                searchResults.map((dish) => (
                                    <div
                                        key={dish.id}
                                        onClick={() => handleAddDish(dish)}
                                        className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-primary-50 cursor-pointer transition-colors"
                                    >
                                        <div>
                                            <p className="text-sm font-medium">{dish.name}</p>
                                            <p className="text-[10px] text-text-muted">
                                                {dish.category} · {dish.process_type} · {dish.main_ingredients.join(', ')}
                                            </p>
                                        </div>
                                        <span className="text-xs text-primary-600 font-medium">¥{dish.cost_per_serving}</span>
                                    </div>
                                ))
                            ) : searchQuery ? (
                                <p className="text-xs text-text-muted text-center py-6">未找到匹配菜品</p>
                            ) : (
                                <p className="text-xs text-text-muted text-center py-6">请输入关键词搜索</p>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

/** 指标卡片组件 */
function MetricCard({
    icon,
    label,
    value,
    color,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
    color: 'primary' | 'accent' | 'warm' | 'red';
}) {
    const colorMap = {
        primary: 'from-primary-50 to-primary-100 text-primary-600 border-primary-200',
        accent: 'from-accent-50 to-accent-100 text-accent-600 border-accent-200',
        warm: 'from-warm-50 to-warm-100 text-warm-600 border-warm-200',
        red: 'from-red-50 to-red-100 text-red-500 border-red-200',
    };

    return (
        <div className={`px-3.5 py-2.5 rounded-xl bg-gradient-to-br border ${colorMap[color]} flex items-center gap-2.5`}>
            <div className="opacity-60">{icon}</div>
            <div>
                <p className="text-[10px] opacity-70">{label}</p>
                <p className="text-sm font-bold">{value}</p>
            </div>
        </div>
    );
}
