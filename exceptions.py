class CheckTokensError(Exception):
    """Исключение проверки токенов."""

    pass


class SendMessageError(Exception):
    """Исключение проверки сообщения."""

    pass


class GetApiAnswerError(Exception):
    """Исключение получения Api ."""

    pass


class GetApiError(Exception):
    """Исключение получения Api ."""

    pass


class CheckResponseError(Exception):
    """Исключение проверки статуса."""

    pass


class ParseStatusError(Exception):
    """Исключение проверки статуса и имени домашки."""

    pass
