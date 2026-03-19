# モデルの絶対: model import
from MonsterHunterWorld.models import Weapon, Armor, Charm, Skill, Monster, Decoration


# ===============================
# スコア計算: calculating scores
# ===============================

def score_weapon(monster, weapon):
    score = weapon.attack_raw or 0

    # 属性ボーナス: bonus for same element with monster weakness
    if weapon.element:
        for w in monster.weaknesses.all():
            if w.kind == "element" and w.name.lower() == weapon.element.lower():
                score += (w.stars or 1) * 30

    # affinity補正: bonus for affinity
    score += (weapon.affinity or 0) * 0.25
    return score


def score_armor(monster, armor):
    """
    防具スコア:
    ・防御力
    ・付与スキルの合計レベル
    ・モンスター属性に対する耐性ボーナス

    armor core:
    - defence power
    - skill level
    - bonus for resistance which same with monster's primary element
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
                resistance_bonus = resistance_value * 30

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

        # 防具と同じスキルならボーナス: bonus for same skill with armors
        if sk.skill.name in armor_skill_names:
            synergy_bonus += 25  

    return base_score + synergy_bonus


def score_decoration(decoration, armor_skill_names):
    score = 0

    for sk in decoration.decoration_skills.all():
        score += sk.skill.max_level * 8

        # Armorと同じスキルならシナジー : bonus for same skill with armors
        if sk.skill.name in armor_skill_names:
            score += 20

    return score


def select_decorations_for_armor(armor, decorations):

    slots = [armor.slot_1, armor.slot_2, armor.slot_3]
    slots = [s for s in slots if s != 0]

    armor_skill_names = {
        sk.skill.name for sk in armor.armor_skills.all()
    }

    selected = []

    for slot_level in slots:

        # スロットと一致するDecorationのみ: check the name of decoration with slot number
        possible = [
            d for d in decorations
            if int(d.name[-1]) == slot_level
        ]

        if not possible:
            continue

        best = max(
            possible,
            key=lambda d: score_decoration(d, armor_skill_names)
        )

        selected.append(best)

    return selected


def score_armor_total(monster, armor, decorations):

    base = score_armor(monster, armor)

    decs = select_decorations_for_armor(armor, decorations)

    dec_score = 0

    armor_skill_names = {
        sk.skill.name for sk in armor.armor_skills.all()
    }

    for d in decs:
        dec_score += score_decoration(d, armor_skill_names)

    return base + dec_score

def collect_skill_levels(head, chest, legs, gloves, waist, charm, decorations):
    skill_levels = {}

    armors = [head, chest, legs, gloves, waist]

    # armor skills
    for armor in armors:
        if not armor:
            continue
        for sk in armor.armor_skills.all():
            name = sk.skill.name
            lvl = sk.level

            skill_levels[name] = skill_levels.get(name, 0) + lvl

    # charm skills
    if charm:
        for sk in charm.charm_skills.all():
            name = sk.skill.name
            lvl = sk.level
            skill_levels[name] = skill_levels.get(name, 0) + lvl

    # decoration skills
    for dec_list in decorations.values():
        for d in dec_list:
            for sk in d.decoration_skills.all():
                name = sk.skill.name
                lvl = sk.level
                skill_levels[name] = skill_levels.get(name, 0) + lvl

    return skill_levels


def apply_skill_caps(skill_levels):
    capped = {}

    for name, lvl in skill_levels.items():

        try:
            skill = Skill.objects.get(name=name)
            max_lvl = skill.max_level
        except Skill.DoesNotExist:
            max_lvl = lvl

        capped[name] = min(lvl, max_lvl)

    return capped

# ===============================
# 軽量ビルド生成: creating the best build
# ===============================

def best_build_fast(monster):


    weapons = list(Weapon.objects.all())
    charms = list(Charm.objects.all())
    decorations = list(Decoration.objects.all())

    armors = {
        "head": list(Armor.objects.filter(armor_type="head")),
        "chest": list(Armor.objects.filter(armor_type="chest")),
        "legs": list(Armor.objects.filter(armor_type="legs")),
        "gloves": list(Armor.objects.filter(armor_type="gloves")),
        "waist": list(Armor.objects.filter(armor_type="waist")),
    }

    # --- スコア順に並べる: sorting socre order ---
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


    # --- 防具トップ決定: confirming the best armor ---
    best_head = heads_sorted[0] if heads_sorted else None
    best_chest = chests_sorted[0] if chests_sorted else None
    best_legs = legs_sorted[0] if legs_sorted else None
    best_gloves = gloves_sorted[0] if gloves_sorted else None
    best_waist = waist_sorted[0] if waist_sorted else None

    # --- 防具スキル取得: getting armor skill type ---
    armor_skill_names = get_armor_skill_names(
        best_head,
        best_chest,
        best_legs,
        best_gloves,
        best_waist
    )


    charms_sorted = sorted(
        charms,
        key=lambda c: score_charm(c, armor_skill_names),
        reverse=True
    )

    best_charm = charms_sorted[0] if charms_sorted else None

    # --- 上位1件ずつ選択: choosing the top score of each part ---
    best_build = {
        "weapon": weapons_sorted[0] if weapons_sorted else None,
        "head": best_head,
        "chest": best_chest,
        "legs": best_legs,
        "gloves": best_gloves,
        "waist": best_waist,
        "charm": best_charm,
        "decorations": {
            "head": select_decorations_for_armor(best_head, decorations),
            "chest": select_decorations_for_armor(best_chest, decorations),
            "legs": select_decorations_for_armor(best_legs, decorations),
            "gloves": select_decorations_for_armor(best_gloves, decorations),
            "waist": select_decorations_for_armor(best_waist, decorations),
        }
    }

    raw_skill_levels = collect_skill_levels(
        best_head,
        best_chest,
        best_legs,
        best_gloves,
        best_waist,
        best_charm,
        best_build["decorations"]
    )

    final_skill_levels = apply_skill_caps(raw_skill_levels)

    best_build["skills"] = final_skill_levels


    return best_build