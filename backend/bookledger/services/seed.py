from sqlmodel import Session, select

from bookledger.models import Tag

DEFAULT_TAGS = [
    ("ignored", "Ignored", "#9ca3af"),
    ("kids", "Kids / picture book", "#facc15"),
    ("ya", "Young adult", "#a78bfa"),
    ("comic", "Comic / graphic novel", "#fb7185"),
    ("reference", "Reference", "#22d3ee"),
    ("religious", "Religious", "#f97316"),
    ("textbook", "Textbook", "#94a3b8"),
    ("low-priority", "Low priority", "#cbd5e1"),
    ("wishlist", "Wishlist", "#34d399"),
    ("favorite-author", "Favorite author", "#f472b6"),
    ("audiobook-may-not-exist", "Audiobook may not exist", "#64748b"),
    ("needs-review", "Needs review", "#fb923c"),
]


def seed_default_tags(session: Session) -> int:
    existing = session.exec(select(Tag.slug)).all()
    existing_set = set(existing)
    inserted = 0
    for slug, label, color in DEFAULT_TAGS:
        if slug in existing_set:
            continue
        session.add(Tag(slug=slug, label=label, color=color, is_filter=True))
        inserted += 1
    if inserted:
        session.commit()
    return inserted
