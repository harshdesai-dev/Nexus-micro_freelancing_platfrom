"""JSON-safe, non-sensitive API representations."""


def user_to_dict(user):
    return {
        "id": str(user.id),
        "name": user.name or f"{user.first_name} {user.last_name}".strip() or user.username,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "account_status": user.account_status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }
