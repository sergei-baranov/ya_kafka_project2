import json


class Payload:
    def __init__(self, message: str, dummy: str = ''):
        self.message = message
        self.dummy = dummy

    def serialize(self) -> bytes:
        return json.dumps({
            'message': self.message,
            'dummy': self.dummy,
        }).encode()


def deserialize2payload(payload: bytes) -> Payload:
    try:
        dct: dict[str, str] = json.loads(payload.decode())
    except json.JSONDecodeError:
        dct: dict[str, str] = {'message': '', 'dummy': '', }
    message = dct.get('message', '')
    dummy = dct.get('dummy', '')

    return Payload(message=message, dummy=dummy)
