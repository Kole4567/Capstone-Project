from django import template

register = template.Library()

@register.filter
def monster_icon(monster_name):
    filename = monster_name.replace(" ", "_").replace("-", "_")
    return f"images/monsters_icon/MHW_{filename}_Icon.webp"

@register.filter
def weapon_icon(weapon_type):
    # Normalize separators
    normalized = (
        weapon_type
        .replace("-", " ")
        .replace("&", " and ")
    )

    parts = normalized.split()

    filename_parts = []
    for word in parts:
        if word.lower() == "and":
            filename_parts.append("and")
        else:
            filename_parts.append(word.capitalize())

    filename = "_".join(filename_parts)

    return f"images/weapons_icon/{filename}_Icon_White.webp"