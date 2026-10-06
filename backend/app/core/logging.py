import logging
import json
import uuid
from datetime import datetime, timezone
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='-')


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        standard={'name','msg','args','levelname','levelno','pathname','filename','module','exc_info','exc_text','stack_info','lineno','funcName','created','msecs','relativeCreated','thread','threadName','processName','process','message','request_id'}
        item={'timestamp':datetime.fromtimestamp(record.created,timezone.utc).isoformat(),'level':record.levelname,'logger':record.name,'request_id':getattr(record,'request_id','-'),'message':record.getMessage()}
        item.update({k:v for k,v in record.__dict__.items() if k not in standard and isinstance(v,(str,int,float,bool,type(None)))})
        return json.dumps(item,ensure_ascii=False,separators=(',',':'))


def configure_logging(level: str = 'INFO') -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())


def new_request_id() -> str:
    return uuid.uuid4().hex

