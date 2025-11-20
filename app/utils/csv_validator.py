class CSVValidator:
    
    REQUIRED_FIELDS = ['sku', 'name']
    
    @staticmethod
    def validate_row(row: dict, row_number: int) -> tuple[bool, str]:
        for field in CSVValidator.REQUIRED_FIELDS:
            if not row.get(field) or str(row.get(field)).strip() == '':
                return False, f"Row {row_number}: Missing required field '{field}'"
        
        # Price is optional, but if present, must be valid
        if row.get('price') and str(row.get('price')).strip() != '':
            try:
                price = float(row.get('price'))
                if price < 0:
                    return False, f"Row {row_number}: Price cannot be negative"
            except (ValueError, TypeError):
                return False, f"Row {row_number}: Invalid price format"
        
        sku = str(row.get('sku', '')).strip()
        if len(sku) > 255:
            return False, f"Row {row_number}: SKU too long (max 255 characters)"
        
        name = str(row.get('name', '')).strip()
        if len(name) > 500:
            return False, f"Row {row_number}: Name too long (max 500 characters)"
        
        return True, None
    
    @staticmethod
    def normalize_row(row: dict) -> dict:
        # Handle optional price, default to 0.0
        price = 0.0
        if row.get('price') and str(row.get('price')).strip() != '':
            try:
                price = float(row.get('price'))
            except (ValueError, TypeError):
                price = 0.0

        return {
            'sku': str(row.get('sku', '')).strip(),
            'name': str(row.get('name', '')).strip(),
            'description': str(row.get('description', '')).strip(),
            'price': price,
            'active': str(row.get('active', 'true')).lower() in ('true', '1', 'yes', 'active')
        }
