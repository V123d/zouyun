/* ========== 走云AI营养排菜 — 核心类型定义 ========== */

/** 灶别标准（已扩展为通用标识，与 quota_profile_id 配合使用） */
export type KitchenClass = string;

/** 配额配置文件数据模型 */
export interface QuotaProfile {
    id: number;
    class_type: string;
    name: string;
    description: string;
    quotas: Record<string, number>;
    quota_type: 'nutrition';
    is_system: boolean;
}

/** 配额配置文件列表项（创建/更新用） */
export interface QuotaProfileCreate {
    class_type: string;
    name: string;
    description?: string;
    quotas: Record<string, number>;
    quota_type?: 'nutrition';
    is_system?: boolean;
}

/** 汤性要求 (已废弃) */

export interface DishCategory {
    name: string;
    count: number;
}

/** 量化食材（无分类字段，仅含名称和克数） */
export interface IngredientQuantified {
    name: string;
    amount_g: number;
}

/** 汤品要求 */
export interface SoupRequirement {
    description: string;
}

/** 餐次特定约束 */
export interface MealSpecificConstraints {
    required_ingredients: string[];
    mandatory_dishes: string[];
    /** 个人菜品结构：每人每餐各分类的菜品数量 */
    personal_dish_structure: {
        categories: DishCategory[];
    };
}

/** 单餐次配置 */
export interface MealConfig {
    id: string;
    meal_name: string;
    enabled: boolean;
    diners_count: number;
    intake_rate: number;
    budget_per_person: number;
    meal_specific_constraints: MealSpecificConstraints;
    dish_structure: {
        categories: DishCategory[];
    };
    staple_types: string[];
    soup_requirements: SoupRequirement;
    flavor_preferences: string;
}

/** 健康状态配置 */
export interface HealthCondition {
    condition: string;
    count: number;
    enabled: boolean;
}

/** 饮食禁忌配置 */
export interface DietaryRestriction {
    restriction: string;
    count: number;
    enabled: boolean;
}

/** 全局硬约束 */
export interface GlobalHardConstraints {
    red_lines: string[];
    health_conditions: HealthCondition[];
    dietary_restrictions: DietaryRestriction[];
}

/** 全局上下文 */
export interface ContextOverview {
    kitchen_class: KitchenClass;
    quota_profile_id: number;
    city: string;
    schedule: {
        start_date: string;
        end_date: string;
    };
    /** 是否包含周末（默认 false，只排工作日） */
    include_weekends: boolean;
}

/** 完整的排菜规则配置 */
export interface MenuPlanConfig {
    context_overview: ContextOverview;
    global_hard_constraints: GlobalHardConstraints;
    meals_config: MealConfig[];
}

/** 菜品信息 */
export interface DishInfo {
    id: number;
    name: string;
    category: string;
    ingredients_quantified: IngredientQuantified[];
    applicable_meals: string[];
    flavor: string;
    cost_per_serving: number;
    nutrition: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
    tags: string[];
    is_manual_added?: boolean;
    /** 排菜份数（由后台计算得出） */
    quantity?: number;
}

/** 灶别标准（已迁移到 QuotaProfile） */
export interface StandardQuota {
    id: number;
    class_type: string;
    quotas: Record<string, number>;
}

/** 单日单格数据 — 日历看板中的单元格 */
export interface CalendarCell {
    date: string;
    meal_name: string;
    category_name: string;
    dishes: DishInfo[];
}

/** 周菜单数据 */
export interface WeeklyMenu {
    [date: string]: {
        [meal_name: string]: {
            [category_name: string]: DishInfo[];
        };
    };
}

/** 灶别标准达标度 */
export interface QuotaCompliance {
    name: string;
    actual: number;
    standard: number;
    rate: number;
    unit?: string;
}

/** 单日营养配额达标数据（SSE推送结构） */
export interface DailyQuotaUpdate {
    date: string;
    quota_compliance: QuotaCompliance[];
    quota_type?: 'nutrition';
}

/** 核心指标汇总 */
export interface DashboardMetrics {
    total_cost: number;
    avg_nutrition_score: number;
    repeat_rate: number;
    alert_count: number;
    alerts?: string[];
    quota_compliance?: QuotaCompliance[];
}

/** 对话消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system';

/** 思考步骤 */
export interface ThinkingStep {
    label: string;
    status: 'pending' | 'running' | 'done' | 'error';
    detail?: string;
}

/** 对话消息 */
export interface ChatMessage {
    id: string;
    role: MessageRole;
    content: string;
    timestamp: number;
    thinking_steps?: ThinkingStep[];
    menu_result?: WeeklyMenu;
    metrics?: DashboardMetrics;
}

/** 智能体信息（来自后端注册表） */
export interface AgentInfo {
    id: string;
    name: string;
    description: string;
    type: 'llm' | 'rule';
    status: 'active' | 'inactive';
    endpoint: string;
}
