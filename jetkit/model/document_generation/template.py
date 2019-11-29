import logging

from themis_doc import Template as ThemisTemplate

from jetkit.db import BaseModel

log = logging.getLogger(__name__)


class Template(ThemisTemplate, BaseModel):
    pass
