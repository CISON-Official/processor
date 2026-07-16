#!/usr/bin/env python3
from pprint import pprint
from functools import wraps
from typing import Callable

from decouple import config
from requests import Session
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def api_caller(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        with Session() as session:
            root_url = str(config("API_URL"))
            email = str(config("API_USEREMAIL"))
            response = session.post(
                root_url + "auth/api-key",
                json=dict(email=email),
            )
            if response.status_code >= 200 and response.status_code < 300:
                data = dict(
                    email=email,
                    token=response.json()["data"]["token"],
                    root_url=root_url,
                    session=session,
                )
                kwargs.update(data)
                return func(*args, **kwargs)
            else:
                raise Exception("Unable to authenticate user {}".format(response.text))

    return wrapper


def setup_header(token) -> dict[str, str]:
    return {"authorization": f"Bearer {token}", "content": "application/json"}


@api_caller
def testing_api_call(name: str, *args, **kwargs) -> None:
    session: Session = kwargs["session"]
    token: str = kwargs["token"]
    root_url: str = kwargs["root_url"]

    response = session.get(root_url + "docs", headers=setup_header(token))
    pprint(response.json())
    print(name)


@api_caller
def create_certification(
    name: str,
    certificate: str,
    cert_key: bytes,
    hmac_key: str,
    user_name: str,
    user_email: str,
    template_id: int = 1,
    is_main: bool = False,
    *args,
    **kwargs,
) -> None:
    session: Session = kwargs["session"]
    token: str = kwargs["token"]
    root_url: str = kwargs["root_url"]

    response = session.post(
        root_url + "certification/create",
        data=dict(
            name=str(name),
            template_id=template_id,
            cert_key=cert_key.decode("utf-8"),
            hmac_key=str(hmac_key),
            user_name=str(user_name),
            user_email=str(user_email),
            is_main=is_main,
        ),
        files=dict(certificate_file=open(certificate, "rb")),
        headers=setup_header(token),
    )
    if response.ok:
        logger.debug(response.text)
        logger.info("Created and sent the   certificates")
        return
    logger.error(response.text)
    return


if __name__ == "__main__":
    testing_api_call("Monkey")
