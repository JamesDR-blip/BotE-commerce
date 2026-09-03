from domain.identity import CurrentUser


class AuthorizationService:
    def authorize(
        self,
        *,
        user: CurrentUser,
        action: str,
        resource: str,
    ) -> None:
        raise NotImplementedError