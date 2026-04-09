import json
import uuid
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import text
from ..database import AsyncSessionLocal
from ..schemas.standard_quota_schema import StandardQuotaCreate, StandardQuotaUpdate, StandardQuotaRead
from typing import List

router = APIRouter(prefix="/api/standard-quotas", tags=["配额配置"])

# 根据 class_type 推断的默认值（仅当数据库中无自定义值时使用）
_KNOWN_DEFAULTS: dict[str, dict] = {
    "一类灶": {
        "name": "一类灶（武警标准）",
        "description": "适用于武警部队一类伙食灶别，每日营养摄入参考标准",
        "quota_type": "ingredient",
    },
    "二类灶": {
        "name": "二类灶（武警标准）",
        "description": "适用于武警部队二类伙食灶别，每日营养摄入参考标准",
        "quota_type": "ingredient",
    },
    "三类灶": {
        "name": "三类灶（武警标准）",
        "description": "适用于武警部队三类伙食灶别，每日营养摄入参考标准",
        "quota_type": "ingredient",
    },
}

_SELECT_SQL = (
    "SELECT id, class_type, quotas, is_system, "
    "COALESCE(name, '') AS name, COALESCE(description, '') AS description, "
    "COALESCE(quota_type, 'ingredient') AS quota_type FROM standard_quotas"
)


def _inject_defaults(row: dict) -> dict:
    """quotas 字符串转 dict；name/description/quota_type 以数据库为准，空则回退内置默认"""
    ct = row.get("class_type", "")
    defaults = _KNOWN_DEFAULTS.get(ct, {
        "name": ct or "",
        "description": "",
        "quota_type": "ingredient",
    })
    quotas_val = row.get("quotas")
    if isinstance(quotas_val, str):
        quotas_val = json.loads(quotas_val)

    name = row.get("name")
    if isinstance(name, str) and name.strip():
        name = name.strip()
    else:
        name = defaults["name"]

    desc = row.get("description")
    if isinstance(desc, str) and desc.strip():
        description = desc.strip()
    else:
        description = defaults.get("description", "")

    qt = row.get("quota_type")
    if isinstance(qt, str) and qt.strip() in ("ingredient", "nutrition"):
        quota_type = qt.strip()
    else:
        quota_type = defaults["quota_type"]

    return {
        "id": row["id"],
        "class_type": row["class_type"],
        "quotas": quotas_val,
        "is_system": row["is_system"],
        "name": name,
        "description": description,
        "quota_type": quota_type,
    }


@router.get("/", response_model=List[StandardQuotaRead])
async def get_all_quotas():
    """获取所有灶别标准"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(_SELECT_SQL))
        rows = result.fetchall()
        cols = result.keys()
        records = [dict(zip(cols, row)) for row in rows]
        return [_inject_defaults(r) for r in records]


@router.post("/", response_model=StandardQuotaRead, status_code=status.HTTP_201_CREATED)
async def create_quota(quota_in: StandardQuotaCreate):
    """创建新配额配置文件"""
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text("SELECT id FROM standard_quotas WHERE class_type = :class_type"),
            {"class_type": quota_in.class_type},
        )
        if existing.fetchone():
            raise HTTPException(status_code=400, detail="该标识的配置已存在")

        await session.execute(
            text(
                "INSERT INTO standard_quotas "
                "(class_type, quotas, is_system, name, description, quota_type) "
                "VALUES (:class_type, :quotas, :is_system, :name, :description, :quota_type)"
            ),
            {
                "class_type": quota_in.class_type,
                "quotas": json.dumps(quota_in.quotas),
                "is_system": quota_in.is_system,
                "name": quota_in.name or "",
                "description": quota_in.description or "",
                "quota_type": quota_in.quota_type or "ingredient",
            },
        )
        await session.commit()

        row = await session.execute(
            text(_SELECT_SQL + " WHERE class_type = :class_type"),
            {"class_type": quota_in.class_type},
        )
        record = dict(zip(row.keys(), row.fetchone()))
        return _inject_defaults(record)


@router.put("/{quota_id}", response_model=StandardQuotaRead)
async def update_quota(quota_id: int, quota_in: StandardQuotaUpdate):
    """更新配额配置文件"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(_SELECT_SQL + " WHERE id = :id"),
            {"id": quota_id},
        )
        record = result.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="配额配置文件不存在")

        cols = result.keys()
        current = dict(zip(cols, record))

        ud = quota_in.model_dump(exclude_unset=True)

        if current["is_system"] and "class_type" in ud and ud["class_type"] not in (None, current["class_type"]):
            raise HTTPException(status_code=403, detail="系统内置配置的标识不可修改")
        class_type_val = ud.get("class_type", current["class_type"])

        quotas_val = current["quotas"]
        if isinstance(quotas_val, str):
            quotas_val = json.loads(quotas_val)
        if "quotas" in ud and ud["quotas"] is not None:
            quotas_json = json.dumps(ud["quotas"])
        else:
            quotas_json = json.dumps(quotas_val)

        name_val = ud["name"] if "name" in ud else (current.get("name") or "")
        desc_val = ud["description"] if "description" in ud else (current.get("description") or "")
        qt_val = ud["quota_type"] if "quota_type" in ud else (current.get("quota_type") or "ingredient")

        await session.execute(
            text(
                "UPDATE standard_quotas SET class_type=:class_type, quotas=:quotas, "
                "name=:name, description=:description, quota_type=:quota_type WHERE id=:id"
            ),
            {
                "class_type": class_type_val,
                "quotas": quotas_json,
                "name": name_val or "",
                "description": desc_val or "",
                "quota_type": qt_val or "ingredient",
                "id": quota_id,
            },
        )
        await session.commit()

        updated = await session.execute(text(_SELECT_SQL + " WHERE id=:id"), {"id": quota_id})
        row = updated.fetchone()
        return _inject_defaults(dict(zip(updated.keys(), row)))


@router.post("/duplicate/{quota_id}", response_model=StandardQuotaRead, status_code=status.HTTP_201_CREATED)
async def duplicate_quota(quota_id: int, new_name: str = Query(..., description="新配置名称")):
    """复制配额配置文件（以指定名称创建副本）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(_SELECT_SQL + " WHERE id=:id"), {"id": quota_id})
        original = result.fetchone()
        if not original:
            raise HTTPException(status_code=404, detail="配额配置文件不存在")

        cols = result.keys()
        orig = dict(zip(cols, original))
        new_class_type = f"custom_{uuid.uuid4().hex[:8]}"

        orig_quotas = orig["quotas"]
        if isinstance(orig_quotas, str):
            orig_quotas = json.loads(orig_quotas)

        await session.execute(
            text(
                "INSERT INTO standard_quotas "
                "(class_type, quotas, is_system, name, description, quota_type) "
                "VALUES (:class_type, :quotas, 0, :name, :description, :quota_type)"
            ),
            {
                "class_type": new_class_type,
                "quotas": json.dumps(orig_quotas),
                "name": new_name,
                "description": orig.get("description") or "",
                "quota_type": orig.get("quota_type") or "ingredient",
            },
        )
        await session.commit()

        row = await session.execute(
            text(_SELECT_SQL + " WHERE class_type=:ct"),
            {"ct": new_class_type},
        )
        record = dict(zip(row.keys(), row.fetchone()))
        return _inject_defaults(record)


@router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota(quota_id: int):
    """删除配额配置文件（系统内置不可删除）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT is_system FROM standard_quotas WHERE id=:id"),
            {"id": quota_id},
        )
        record = result.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="配额配置文件不存在")
        if record[0]:
            raise HTTPException(status_code=403, detail="系统内置配置不可删除")

        await session.execute(text("DELETE FROM standard_quotas WHERE id=:id"), {"id": quota_id})
        await session.commit()
        return None
