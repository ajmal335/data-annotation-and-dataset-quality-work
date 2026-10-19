"""Extract labeled fields from OCR text and return auditable validation issues.

This baseline accepts a deliberately narrow invoice format; it does not perform OCR.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import re

LABELS = {
    'invoice number': 'invoice_number', 'invoice no': 'invoice_number',
    'invoice date': 'invoice_date', 'date': 'invoice_date',
    'currency': 'currency', 'subtotal': 'subtotal', 'tax': 'tax', 'total': 'total',
}
REQUIRED = ('invoice_number', 'invoice_date', 'currency', 'subtotal', 'tax', 'total')
MONEY = re.compile(r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?\Z')

def validate_invoice(text: str) -> dict:
    if not isinstance(text, str) or not text.strip() or len(text) > 20000:
        raise ValueError('Provide 1–20,000 characters of invoice text')
    fields, evidence, issues = {}, {}, []
    duplicates = set()
    for number, line in enumerate(text.splitlines(), 1):
        label, separator, value = line.partition(':')
        if not separator:
            continue
        field = LABELS.get(' '.join(label.casefold().split()))
        if field is None:
            continue
        value = value.strip()
        evidence.setdefault(field, []).append({'line': number, 'value': value})
        if field in fields:
            duplicates.add(field)
        else:
            fields[field] = value
    for field in REQUIRED:
        if not fields.get(field):
            issues.append({'code': 'missing_field', 'field': field})
    for field in sorted(duplicates):
        issues.append({'code': 'duplicate_field', 'field': field})
    if fields.get('invoice_date'):
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fields['invoice_date']):
                raise ValueError
            date.fromisoformat(fields['invoice_date'])
        except ValueError:
            issues.append({'code': 'invalid_date', 'field': 'invoice_date'})
    if fields.get('currency') and fields['currency'] not in {'PKR', 'USD', 'AED', 'EUR', 'GBP'}:
        issues.append({'code': 'unsupported_currency', 'field': 'currency'})
    amounts = {}
    for field in ('subtotal', 'tax', 'total'):
        value = fields.get(field)
        if not value or field in duplicates:
            continue
        if not MONEY.fullmatch(value):
            issues.append({'code': 'invalid_amount', 'field': field})
            continue
        amounts[field] = Decimal(value.replace(',', ''))
        fields[field] = format(amounts[field], '.2f')
    if len(amounts) == 3 and amounts['subtotal'] + amounts['tax'] != amounts['total']:
        issues.append({'code': 'total_mismatch', 'field': 'total',
                       'expected': format(amounts['subtotal'] + amounts['tax'], '.2f')})
    return {'valid': not issues, 'fields': fields, 'evidence': evidence, 'issues': issues,
            'method': 'labeled-text-rules-v1'}
