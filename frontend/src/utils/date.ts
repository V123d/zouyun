/* ========== 日期工具函数 ========== */

/** 获取日期范围内的所有日期字符串 (YYYY-MM-DD) */
export function getDateRange(startDate: string, endDate: string): string[] {
    const dates: string[] = [];
    const start = new Date(startDate);
    const end = new Date(endDate);
    const current = new Date(start);

    while (current <= end) {
        dates.push(current.toISOString().split('T')[0]);
        current.setDate(current.getDate() + 1);
    }

    return dates;
}

/** 获取星期几的中文显示 */
export function getWeekdayLabel(dateStr: string): string {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const date = new Date(dateStr);
    return weekdays[date.getDay()];
}

/** 格式化日期为 MM.DD 格式 */
export function formatDateShort(dateStr: string): string {
    const date = new Date(dateStr);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}.${date.getDate().toString().padStart(2, '0')}`;
}

/** 生成唯一 ID */
export function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}
