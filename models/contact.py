from dataclasses import dataclass
from typing import List

@dataclass
class Contact:
    name: str
    phone: str
    present_address: str = ""
    permanent_address: str = ""
    driver_license: str = ""
    passport_no: str = ""
    nid_no: str = ""
    notes: str = ""
    profile_pic: str = ""           # file path
    attachments: List[str] = None   # list of file paths

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []

@dataclass
class ContactSummary:
    id: int
    name: str
    phone: str
    profile_pic: str
