from typing import Annotated
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from quality_tools.invoices import validate_invoice
from quality_tools.yolo import validate_yolo

app = FastAPI(title='Document & Annotation Quality API', version='1.0.0')

class InvoiceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]

class YoloRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: Annotated[str, StringConstraints(max_length=100000)]
    class_count: int = Field(strict=True, ge=1, le=10000)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/invoices/validate')
def invoice(payload: InvoiceRequest):
    return validate_invoice(payload.text)

@app.post('/annotations/yolo/validate')
def yolo(payload: YoloRequest):
    return validate_yolo(payload.text, payload.class_count)
