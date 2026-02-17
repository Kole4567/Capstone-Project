import os
import sys
from itertools import product

# build_logic_api.py の場所: Capstone-Project/mysite/MonsterHunterWorld/
# mysite までを sys.path に追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # → mysite
sys.path.insert(0, BASE_DIR)

# Django 設定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")  # 修正

import django
django.setup()

# モデルの絶対 import
from MonsterHunterWorld.models import Weapon, Armor, Charm, Skill, Monster


# ===============================
# スコア計算
# ===============================

def score_weapon(monster, weapon):
    score = weapon.attack_raw or 0

    # 属性ボーナス
    if weapon.element:
        for w in monster.weaknesses.all():
            if w.kind == "element" and w.name.lower() == weapon.element.lower():
                score += (w.stars or 1) * 30

    # affinity補正
    score += (weapon.affinity or 0) * 0.25
    return score


def score_armor(monster, armor):
    """
    防具スコア:
    ・防御力
    ・付与スキルの合計レベル
    ・モンスター属性に対する耐性ボーナス
    """

    defense_score = armor.defense_max or 0
    skill_score = sum(sk.skill.max_level for sk in armor.armor_skills.all()) * 10

    resistance_bonus = 0

    if monster.primary_element:
        element = monster.primary_element.lower()
        resistance_field = f"res_{element}"

        if hasattr(armor, resistance_field):
            resistance_value = getattr(armor, resistance_field) or 0

            if resistance_value >= 0:
                resistance_bonus = resistance_value * 15
            else:
                resistance_bonus = resistance_value * 30  # 弱点は重く

    return defense_score + skill_score + resistance_bonus


def get_armor_skill_names(*armors):
    skill_names = set()

    for armor in armors:
        if armor:
            for sk in armor.armor_skills.all():
                skill_names.add(sk.skill.name)

    return skill_names


def score_charm(charm, armor_skill_names):
    base_score = 0
    synergy_bonus = 0

    for sk in charm.charm_skills.all():
        base_score += sk.skill.max_level * 10

        # 防具と同じスキルならボーナス
        if sk.skill.name in armor_skill_names:
            synergy_bonus += 25   # ← 調整可能

    return base_score + synergy_bonus


# ===============================
# 軽量ビルド生成
# ===============================

def best_build_fast(monster):
    """
    部位ごとにスコア順でソートし、
    それぞれの1位を組み合わせる軽量方式
    """

    weapons = list(Weapon.objects.all())
    charms = list(Charm.objects.all())

    armors = {
        "head": list(Armor.objects.filter(armor_type="head")),
        "chest": list(Armor.objects.filter(armor_type="chest")),
        "legs": list(Armor.objects.filter(armor_type="legs")),
        "gloves": list(Armor.objects.filter(armor_type="gloves")),
        "waist": list(Armor.objects.filter(armor_type="waist")),
    }

    # --- スコア順に並べる ---
    weapons_sorted = sorted(
        weapons,
        key=lambda w: score_weapon(monster, w),
        reverse=True
    )

    heads_sorted = sorted(
    armors["head"],
    key=lambda a: score_armor(monster, a),
    reverse=True
    )

    chests_sorted = sorted(
    armors["chest"],
    key=lambda a: score_armor(monster, a),
    reverse=True
    )

    legs_sorted = sorted(
    armors["legs"],
    key=lambda a: score_armor(monster, a),
    reverse=True
    )

    gloves_sorted = sorted(
    armors["gloves"],
    key=lambda a: score_armor(monster, a),
    reverse=True
    )

    waist_sorted = sorted(
    armors["waist"],
    key=lambda a: score_armor(monster, a),
    reverse=True
    )


    # --- 防具トップ決定 ---
    best_head = heads_sorted[0] if heads_sorted else None
    best_chest = chests_sorted[0] if chests_sorted else None
    best_legs = legs_sorted[0] if legs_sorted else None
    best_gloves = gloves_sorted[0] if gloves_sorted else None
    best_waist = waist_sorted[0] if waist_sorted else None

    # --- 防具スキル取得 ---
    armor_skill_names = get_armor_skill_names(
        best_head,
        best_chest,
        best_legs,
        best_gloves,
        best_waist
    )

    # --- シナジー込みでCharm再評価 ---
    charms_sorted = sorted(
        charms,
        key=lambda c: score_charm(c, armor_skill_names),
        reverse=True
    )

    best_charm = charms_sorted[0] if charms_sorted else None

    # --- 上位1件ずつ選択 ---
    best_build = {
        "weapon": weapons_sorted[0] if weapons_sorted else None,
        "head": best_head,
        "chest": best_chest,
        "legs": best_legs,
        "gloves": best_gloves,
        "waist": best_waist,
        "charm": best_charm,
    }


    return best_build


# ===============================
# 実行
# ===============================

def run_for_monster(monster_name):
    try:
        monster = Monster.objects.get(name=monster_name)
    except Monster.DoesNotExist:
        print(f"Monster '{monster_name}' not found.")
        return

    build = best_build_fast(monster)

    print("\n=== BEST BUILD ===")
    print(f"Monster: {monster.name}\n")

    if build["weapon"]:
        print(f"Weapon: {build['weapon'].name}")
    if build["head"]:
        print(f"Head: {build['head'].name}")
    if build["chest"]:
        print(f"Chest: {build['chest'].name}")
    if build["legs"]:
        print(f"Legs: {build['legs'].name}")
    if build["gloves"]:
        print(f"Gloves: {build['gloves'].name}")
    if build["waist"]:
        print(f"Waist: {build['waist'].name}")
    if build["charm"]:
        print(f"Charm: {build['charm'].name}")


if __name__ == "__main__":
    run_for_monster("Aptonoth")