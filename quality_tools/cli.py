"""Run with python -m quality_tools.cli invoice examples/invoice_valid.txt."""
import argparse
import json
from pathlib import Path
from quality_tools.invoices import validate_invoice
from quality_tools.yolo import validate_yolo

def main():
    parser = argparse.ArgumentParser(description='Audit invoice text or YOLO detection labels')
    parser.add_argument('kind', choices=['invoice', 'yolo'])
    parser.add_argument('path', type=Path)
    parser.add_argument('--classes', type=int, default=2)
    args = parser.parse_args()
    limit = 20000 if args.kind == 'invoice' else 100000
    try:
        with args.path.open(encoding='utf-8') as file:
            text = file.read(limit + 1)
        report = validate_invoice(text) if args.kind == 'invoice' else validate_yolo(text, args.classes)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    return 0 if report['valid'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
