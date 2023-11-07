from howler.services import auth_service


def get_token(user=None):
    if user is None:
        user = "goose"

    return f"{user}:{auth_service.create_token(user, ['R', 'W', 'E'])}"
