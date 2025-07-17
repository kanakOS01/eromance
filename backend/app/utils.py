import re

def generate_unique_slug(title: str, existing_slugs: set[str]) -> str:
    base_slug = re.sub(r"[^\w]+", "-", title.lower()).strip("-")
    slug = base_slug
    suffix = 1

    while slug in existing_slugs:
        slug = f"{base_slug}_{suffix}"
        suffix += 1

    return slug
