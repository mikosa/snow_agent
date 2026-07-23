import json
import pandas as pd
from pathlib import Path
from io import StringIO, BytesIO

def generate_export_csv(session_data, file_store) -> bytes:
    """Generates a CSV export combining all available data."""
    if not session_data.data_state.is_cleaned:
        return b""
        
    try:
        # Load cleaned data
        cleaned_path = file_store.load_artifact(session_data.id, "cleaned.parquet")
        df = pd.read_parquet(cleaned_path)
        
        # Add clusters if available
        if session_data.data_state.is_clustered:
            clusters_path = file_store.load_artifact(session_data.id, "clusters.parquet")
            clusters_df = pd.read_parquet(clusters_path)
            # Assuming clusters_df has cluster_label and matches index
            df["cluster_label"] = clusters_df["cluster_label"]
            
        # Add categories if available
        if session_data.data_state.is_categorized:
            categories_path = file_store.load_artifact(session_data.id, "categories.json")
            with open(categories_path, "r", encoding="utf-8") as f:
                categories = json.load(f)
            # Map cluster_label to category_name
            cat_map = {cat["cluster_id"]: cat["name"] for cat in categories}
            df["category"] = df.get("cluster_label").map(cat_map)
            
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    except Exception as e:
        print(f"Error generating CSV export: {e}")
        return b""

def generate_export_json(session_data, file_store) -> bytes:
    """Generates a JSON hierarchical report."""
    report = {
        "session_id": session_data.id,
        "is_cleaned": session_data.data_state.is_cleaned,
        "is_clustered": session_data.data_state.is_clustered,
        "is_categorized": session_data.data_state.is_categorized,
        "data": {}
    }
    
    if session_data.data_state.is_categorized:
        try:
            categories_path = file_store.load_artifact(session_data.id, "categories.json")
            with open(categories_path, "r", encoding="utf-8") as f:
                report["data"]["categories"] = json.load(f)
        except Exception:
            pass
            
    if session_data.data_state.is_subcategorized:
        try:
            subcat_path = file_store.load_artifact(session_data.id, "subcategories.json")
            with open(subcat_path, "r", encoding="utf-8") as f:
                report["data"]["subcategories"] = json.load(f)
        except Exception:
            pass
            
    if session_data.data_state.is_entities_extracted:
        try:
            entities_path = file_store.load_artifact(session_data.id, "entities.json")
            with open(entities_path, "r", encoding="utf-8") as f:
                report["data"]["entities"] = json.load(f)
        except Exception:
            pass
            
    return json.dumps(report, indent=2).encode('utf-8')

def generate_export_excel(session_data, file_store) -> bytes:
    """Generates a multi-sheet Excel workbook export."""
    excel_buffer = BytesIO()
    
    try:
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                "Metric": ["Session ID", "Cleaned", "Clustered", "Categorized", "Row Count"],
                "Value": [
                    session_data.id, 
                    session_data.data_state.is_cleaned,
                    session_data.data_state.is_clustered,
                    session_data.data_state.is_categorized,
                    session_data.data_state.row_count
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
            
            # Categories sheet
            if session_data.data_state.is_categorized:
                try:
                    categories_path = file_store.load_artifact(session_data.id, "categories.json")
                    with open(categories_path, "r", encoding="utf-8") as f:
                        categories = json.load(f)
                    pd.DataFrame(categories).to_excel(writer, sheet_name="Categories", index=False)
                except Exception:
                    pass
            
            # All Tickets sheet
            if session_data.data_state.is_cleaned:
                try:
                    cleaned_path = file_store.load_artifact(session_data.id, "cleaned.parquet")
                    df = pd.read_parquet(cleaned_path)
                    
                    if session_data.data_state.is_clustered:
                        clusters_path = file_store.load_artifact(session_data.id, "clusters.parquet")
                        clusters_df = pd.read_parquet(clusters_path)
                        df["cluster_label"] = clusters_df["cluster_label"]
                        
                    df.to_excel(writer, sheet_name="All Tickets", index=False)
                except Exception:
                    pass
                    
        return excel_buffer.getvalue()
    except Exception as e:
        print(f"Error generating Excel export: {e}")
        return b""
