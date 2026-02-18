from django import template

register = template.Library()

@register.filter
def monster_icon(monster_name):
    filename = monster_name.replace(" ", "_").replace("-", "_")
    return f"images/monsters_icon/MHW_{filename}_Icon.webp"