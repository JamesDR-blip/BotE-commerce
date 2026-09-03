from domain.identity import CurrentUser


class AuthenticationService:
    def authenticate(self, token: str) -> CurrentUser:
        raise NotImplementedError
