class ConnectionFailure(Exception):
    def __init__(self, resp_code: int, msg: str):
        super().__init__(
            f"Connection failed | Response code: {resp_code} | Error message: {msg}"
        )


class JSONDecodeFailure(Exception):
    pass
