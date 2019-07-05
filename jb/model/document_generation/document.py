import logging

from themis_doc import Document as ThemisDocument

from jb.db import BaseModel

log = logging.getLogger(__name__)


class Document(ThemisDocument, BaseModel):
    pass
