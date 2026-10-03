import pandas as pd
from typing import Dict, Any

def get_log_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates basic operational metadata to reduce raw LLM tokens."""
    total_rows = len(df)
    columns = list(df.columns)
    
    # Try detecting log levels if present
    level_col = next((c for c in df.columns if c.lower() in ["level", "log_level", "severity", "status"]), None)
    level_counts = df[level_col].value_counts().to_dict() if level_col else {}
    
    return {
        "total_logs": total_rows,
        "columns": columns,
        "level_counts": level_counts,
    }