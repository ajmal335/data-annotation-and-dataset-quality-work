# Project walkthrough

## Invoice Text Validator

`invoices.py` separates extraction from reporting: recognized labels map to canonical fields, evidence records every recognized occurrence, and validation accumulates issues instead of discarding the document. Duplicate values require review even when they are identical. Decimal avoids binary floating-point errors in financial arithmetic. This is a format validator, not financial advice or authenticity verification.

Try changing the tax, duplicating the total, and entering an impossible date. Inspect both the issue codes and the evidence. Think about how an OCR adapter would supply this text and how a labeled test set would measure extraction accuracy.

## YOLO Annotation Auditor

`yolo.py` checks row shape, class IDs, numeric parsing, finiteness, normalized ranges, full-box bounds, and duplicates in that order. Merely checking centers between zero and one does not ensure the entire box fits. An empty label can be valid for a background image, so absence of objects is distinct from a missing file.

Try a box with center 0.95 and width 0.4: its right edge is 1.15, outside the image. Try `NaN`, a zero-width box, and a class ID equal to the class count.

## API and CLI

The same pure validation functions power both interfaces. Pydantic checks the HTTP input contract; the validators enforce domain rules. A syntactically valid request containing a bad invoice returns a report, not an HTTP error. The CLI returns a nonzero exit status for a failed audit so a pipeline can stop.

## Before interviewing

Run the tests, make one improvement yourself, and explain why an OCR confidence score and a document validation result are different. These projects were developed with AI assistance and have not been deployed for a client.
