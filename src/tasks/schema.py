#!/usr/bin/env python3

from pydantic import BaseModel


class CertificatePayload(BaseModel):
    name: str
    certificate_name: str
