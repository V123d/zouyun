import sys
import os
import json
import asyncio

# 将 backend 根目录放入 sys.path，以便正常导入 app 原生模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, AsyncSessionLocal
from app.models.dish import Dish
from app.config import DISH_LIBRARY_PATH

async def run_migration():
    print("正在创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    print(f"正在读取文件 JSON 数据: {DISH_LIBRARY_PATH} ...")
    if not os.path.exists(DISH_LIBRARY_PATH):
        print("错误: 数据文件不存在!")
        return
        
    with open(DISH_LIBRARY_PATH, "r", encoding="utf-8") as f:
        dishes_data = json.load(f)
        
    print(f"准备导入 {len(dishes_data)} 条菜品...")
    
    async with AsyncSessionLocal() as session:
        # 导入前先清空表
        await session.execute(Dish.__table__.delete())
        
        objects = []
        for d in dishes_data:
            dish_obj = Dish(
                id=d["id"],
                name=d["name"],
                category=d.get("category", "其他"),
                main_ingredients=d.get("main_ingredients", []),
                process_type=d.get("process_type", "未知"),
                flavor=d.get("flavor", "未知"),
                cost_per_serving=d.get("cost_per_serving", 0.0),
                nutrition=d.get("nutrition", {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}),
                tags=d.get("tags", [])
            )
            objects.append(dish_obj)
            
        session.add_all(objects)
        await session.commit()
    
    print("导入完成！✅")

if __name__ == "__main__":
    asyncio.run(run_migration())
