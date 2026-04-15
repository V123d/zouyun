/* ========== 全局概览区 (Context Header) ========== */
import { Calendar, MapPin, School, Users } from 'lucide-react';
import { useAppStore } from '../../stores/app-store';

export default function ContextHeader() {
    const { config } = useAppStore();
    const { kitchen_class, city, schedule } = config.context_overview;
    const enabledMeals = config.meals_config.filter((m) => m.enabled);

    return (
        <div className="px-4 py-3 border-b border-border-light bg-white/60 backdrop-blur-sm">
            {/* 标题行 */}
            <div className="flex items-center gap-2 mb-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-sm">
                    <span className="text-white text-sm">🍽️</span>
                </div>
                <h1 className="text-base font-bold text-text-primary">走云AI营养排菜</h1>
                <span className="text-xs text-text-muted ml-1">智能排菜系统</span>
            </div>

            {/* 场景信息标签 */}
            <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                    <School size={12} />
                    {kitchen_class}
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-accent-50 text-accent-700 rounded-full text-xs font-medium">
                    <MapPin size={12} />
                    {city}
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                    <Calendar size={12} />
                    {schedule.start_date.slice(5)} ~ {schedule.end_date.slice(5)}
                </span>
            </div>

            {/* 餐次人数标签 */}
            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                {enabledMeals.map((meal) => (
                    <span
                        key={meal.id}
                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-warm-50 text-warm-700 rounded-md text-xs"
                    >
                        <Users size={10} />
                        {meal.meal_name}: {meal.diners_count}人
                    </span>
                ))}
            </div>
        </div>
    );
}
