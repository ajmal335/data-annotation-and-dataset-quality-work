from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from quality_tools.api import app
from quality_tools.invoices import validate_invoice
from quality_tools.yolo import validate_yolo

EXAMPLES=Path(__file__).resolve().parents[1]/'examples'
VALID=(EXAMPLES/'invoice_valid.txt').read_text()

def test_invoice_valid_and_evidence():
    result=validate_invoice(VALID)
    assert result['valid']
    assert result['fields']['total']=='1160.00'
    assert result['evidence']['total']==[{'line':7,'value':'1,160.00'}]

@pytest.mark.parametrize('old,new,code',[
    ('2026-10-19','2026-02-30','invalid_date'),
    ('2026-10-19','19/10/2026','invalid_date'),
    ('PKR','XYZ','unsupported_currency'),
    ('1,160.00','1,100.00','total_mismatch'),
    ('1,160.00','1,16.00','invalid_amount'),
    ('1,160.00','NaN','invalid_amount'),
    ('1,160.00','-1.00','invalid_amount'),
    ('1,160.00','1160.001','invalid_amount'),
])
def test_invoice_issues(old,new,code):
    result=validate_invoice(VALID.replace(old,new))
    assert not result['valid']
    assert code in {i['code'] for i in result['issues']}

def test_duplicate_alias_preserves_evidence():
    result=validate_invoice(VALID+'\nInvoice No: DIFFERENT')
    assert not result['valid']
    assert result['fields']['invoice_number']=='DEMO-001'
    assert len(result['evidence']['invoice_number'])==2
    assert {'code':'duplicate_field','field':'invoice_number'} in result['issues']

def test_duplicate_amount_does_not_validate_total():
    result=validate_invoice(VALID+'\nTotal: 1.00')
    assert not result['valid']
    assert 'total_mismatch' not in {i['code'] for i in result['issues']}

def test_missing_invoice_fields():
    assert len(validate_invoice('Vendor: demo')['issues'])==6

@pytest.mark.parametrize('text',['',' '*4,'x'*20001])
def test_reject_invalid_invoice_input(text):
    with pytest.raises(ValueError): validate_invoice(text)

def test_decimal_arithmetic():
    text=VALID.replace('1,000.00','0.10').replace('160.00','0.20').replace('1,0.20','0.30')
    assert validate_invoice(text)['valid']

@pytest.mark.parametrize('text,code',[
    ('0 0.5 0.5 0.2','wrong_column_count'),
    ('2 0.5 0.5 0.2 0.2','invalid_class'),
    ('0.5 0.5 0.5 0.2 0.2','invalid_class'),
    ('0 nan 0.5 0.2 0.2','nonfinite_coordinate'),
    ('0 0.5 inf 0.2 0.2','nonfinite_coordinate'),
    ('0 bad 0.5 0.2 0.2','invalid_number'),
    ('0 0.5 0.5 0 0.2','coordinate_out_of_range'),
    ('0 0.95 0.5 0.2 0.2','box_outside_image'),
    ('0 0.5 0.5 0.2 0.2\n0 0.50 0.50 0.20 0.20','duplicate_box'),
])
def test_yolo_errors(text,code):
    result=validate_yolo(text,2)
    assert not result['valid']
    assert result['issues'][0]['code']==code

def test_empty_background_and_boundary_box():
    assert validate_yolo('',2)['empty_label']
    assert validate_yolo('0 0.5 0.5 1 1',2)['valid']
    assert validate_yolo((EXAMPLES/'yolo_valid.txt').read_text(),2)['valid_box_count']==2

@pytest.mark.parametrize('count',[0,-1,True,1.5])
def test_bad_class_count(count):
    with pytest.raises(ValueError): validate_yolo('',count)

def test_api_returns_audit_failures_as_reports():
    client=TestClient(app)
    assert client.get('/health').status_code==200
    response=client.post('/invoices/validate',json={'text':VALID})
    assert response.status_code==200 and response.json()['valid']
    response=client.post('/annotations/yolo/validate',json={'text':'2 0.5 0.5 0.2 0.2','class_count':2})
    assert response.status_code==200 and not response.json()['valid']
    assert client.post('/invoices/validate',json={'text':' '}).status_code==422
    assert client.post('/annotations/yolo/validate',json={'text':'','class_count':True}).status_code==422
