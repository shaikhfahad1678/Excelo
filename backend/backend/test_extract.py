from backend.services.statement_service import StatementService
svc = StatementService()
pdf_path = r'C:\Users\yahya\.gemini\antigravity-ide\brain\032b76b5-1068-4cac-b554-d8057ecb793d\media__1786096262532.pdf'
svc.extraction_results['temp'] = {'file_path': pdf_path, 'filename': 'test.pdf', 'pages': 1}
svc.file_cards['temp'] = {'file_path': pdf_path, 'filename': 'test.pdf', 'pages': 1, 'pdf_type': 'TYPE 1: Native Digital PDF'}

res = svc.extract_file('temp', 'Auto Multi-Engine Pipeline')
print(f'Success: {res.get("success")}')
print(f'Tx count: {len(res.get("transactions", []))}')
print(f'Error: {res.get("error", "None")}')
