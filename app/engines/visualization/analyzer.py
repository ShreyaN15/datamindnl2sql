"""
Data Visualization Analyzer

Analyzes SQL query results to determine if they are visualizable and
recommends appropriate chart types based on data characteristics.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    NOT_VISUALIZABLE = "not_visualizable"


class VisualizationAnalyzer:
    """
    Analyzes query results to determine visualization suitability.
    
    Strategy:
    1. Check if data is visualizable (has numeric/aggregated data)
    2. Detect data patterns (categorical, temporal, numeric)
    3. Recommend appropriate chart type
    4. Format data for frontend charting libraries
    """
    
    def __init__(self):
        self.numeric_types = {'int', 'integer', 'float', 'double', 'decimal', 'numeric', 'real', 'bigint', 'smallint'}
        self.date_types = {'date', 'datetime', 'timestamp', 'time'}
        
    def analyze(
        self,
        query_result: List[Dict[str, Any]],
        column_info: List[Dict[str, str]],
        sql_query: str
    ) -> Dict[str, Any]:
        """
        Analyze query results for visualization.
        
        Args:
            query_result: List of result rows as dicts
            column_info: List of column metadata (name, type)
            sql_query: The SQL query that generated these results
        
        Returns:
            {
                "is_visualizable": bool,
                "reason": str,
                "recommended_chart": str,
                "chart_config": dict,
                "data": formatted data for charts
            }
        """
        # Handle empty results
        if not query_result or len(query_result) == 0:
            return {
                "is_visualizable": False,
                "reason": "No data returned from query",
                "recommended_chart": ChartType.NOT_VISUALIZABLE,
                "chart_config": None,
                "data": None
            }
        
        # Analyze data structure
        num_rows = len(query_result)
        num_columns = len(column_info)
        
        logger.info(f"Analyzing {num_rows} rows × {num_columns} columns for visualization")
        
        # Detect column types
        column_types = self._classify_columns(query_result, column_info)
        
        # Check if visualizable
        is_visualizable, reason = self._check_visualizable(column_types, num_rows, sql_query)
        
        if not is_visualizable:
            return {
                "is_visualizable": False,
                "reason": reason,
                "recommended_chart": ChartType.NOT_VISUALIZABLE,
                "chart_config": None,
                "data": None
            }
        
        # Recommend chart type
        chart_type, chart_config = self._recommend_chart(
            column_types,
            query_result,
            num_rows,
            sql_query
        )
        
        # Format data for visualization
        formatted_data = self._format_data_for_chart(
            query_result,
            column_types,
            chart_type
        )
        
        return {
            "is_visualizable": True,
            "reason": "Data contains visualizable patterns",
            "recommended_chart": chart_type,
            "chart_config": chart_config,
            "data": formatted_data
        }
    
    def _classify_columns(
        self,
        query_result: List[Dict[str, Any]],
        column_info: List[Dict[str, str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Classify each column by data type and characteristics"""
        classifications = {}
        
        for col_meta in column_info:
            col_name = col_meta['name']
            col_type = col_meta.get('type', '').lower()
            
            # Sample values from first few rows
            sample_values = [
                row.get(col_name) 
                for row in query_result[:10] 
                if row.get(col_name) is not None
            ]
            
            # Classify column
            is_numeric = self._is_numeric_column(col_type, sample_values)
            is_date = self._is_date_column(col_type, sample_values)
            # Numeric columns should NOT be categorical (mutually exclusive)
            is_categorical = False if is_numeric else self._is_categorical_column(sample_values, len(query_result))
            
            classifications[col_name] = {
                'type': col_type,
                'is_numeric': is_numeric,
                'is_date': is_date,
                'is_categorical': is_categorical,
                'sample_values': sample_values[:5],
                'unique_count': len(set(str(row.get(col_name)) for row in query_result if row.get(col_name) is not None))
            }
        
        return classifications
    
    def _is_numeric_column(self, col_type: str, sample_values: List[Any]) -> bool:
        """Check if column contains numeric data"""
        # Check by type
        if any(t in col_type for t in self.numeric_types):
            return True
        
        # Check by values
        if sample_values:
            try:
                numeric_count = sum(
                    1 for v in sample_values 
                    if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit())
                )
                return numeric_count / len(sample_values) > 0.8
            except:
                return False
        
        return False
    
    def _is_date_column(self, col_type: str, sample_values: List[Any]) -> bool:
        """Check if column contains date/time data"""
        return any(t in col_type for t in self.date_types)
    
    def _is_categorical_column(self, sample_values: List[Any], total_rows: int) -> bool:
        """Check if column is categorical (limited unique values)"""
        if not sample_values:
            return False
        
        unique_count = len(set(str(v) for v in sample_values))
        
        # Categorical if:
        # 1. Few unique values relative to total (< 20% unique or < 20 total unique)
        # 2. String values that repeat
        if unique_count < 20 or unique_count < total_rows * 0.2:
            return True
        
        return False
    
    def _check_visualizable(
        self,
        column_types: Dict[str, Dict[str, Any]],
        num_rows: int,
        sql_query: str
    ) -> Tuple[bool, str]:
        """Determine if data is suitable for visualization"""
        
        # Count column types
        numeric_cols = [c for c, info in column_types.items() if info['is_numeric']]
        categorical_cols = [c for c, info in column_types.items() if info['is_categorical']]
        date_cols = [c for c, info in column_types.items() if info['is_date']]
        
        # Must have at least one numeric column for most visualizations
        if not numeric_cols:
            # Exception: Can visualize categorical distribution
            if len(categorical_cols) >= 1 and num_rows <= 50:
                return True, "Categorical data suitable for distribution chart"
            
            return False, "No numeric data to visualize. Results contain only text/identifiers which are not suitable for charts."
        
        # Check for meaningful data (not just IDs)
        if num_rows < 2:
            return False, "Insufficient data rows for visualization (need at least 2 rows)"
        
        # Check if all columns are just IDs/identifiers
        all_ids = all(
            'id' in col_name.lower() or 'code' in col_name.lower()
            for col_name in column_types.keys()
        )
        if all_ids:
            return False, "Data contains only identifiers (IDs/codes) which are not meaningful to visualize"
        
        # Check for aggregation keywords in SQL
        sql_upper = sql_query.upper()
        has_aggregation = any(
            keyword in sql_upper 
            for keyword in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP BY']
        )
        
        if has_aggregation and numeric_cols:
            return True, "Aggregated numeric data suitable for visualization"
        
        if numeric_cols and (categorical_cols or date_cols):
            return True, "Data contains both dimensions and measures suitable for visualization"
        
        return True, "Data structure suitable for visualization"
    
    def _recommend_chart(
        self,
        column_types: Dict[str, Dict[str, Any]],
        query_result: List[Dict[str, Any]],
        num_rows: int,
        sql_query: str
    ) -> Tuple[ChartType, Dict[str, Any]]:
        """Recommend the best chart type for the data"""
        
        numeric_cols = [c for c, info in column_types.items() if info['is_numeric']]
        categorical_cols = [c for c, info in column_types.items() if info['is_categorical']]
        date_cols = [c for c, info in column_types.items() if info['is_date']]
        
        sql_upper = sql_query.upper()
        
        # PIE CHART: Best for showing parts of a whole
        # - One categorical dimension + one numeric measure
        # - Limited categories (< 10)
        # - Aggregation query (COUNT, SUM)
        if (len(categorical_cols) == 1 and len(numeric_cols) == 1 and 
            num_rows <= 10 and any(k in sql_upper for k in ['COUNT', 'SUM', 'GROUP BY'])):
            
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            return ChartType.PIE, {
                "title": f"Distribution by {cat_col}",
                "labels_column": cat_col,
                "values_column": num_col,
                "description": f"Shows the proportion of {num_col} across different {cat_col}"
            }
        
        # LINE CHART: Best for trends over time
        # - One date/time column + one or more numeric columns
        if date_cols and numeric_cols:
            date_col = date_cols[0]
            num_col = numeric_cols[0]
            
            return ChartType.LINE, {
                "title": f"{num_col} over time",
                "x_axis": date_col,
                "y_axis": num_col,
                "x_label": date_col,
                "y_label": num_col,
                "description": f"Shows the trend of {num_col} over {date_col}"
            }
        
        # BAR CHART: Best for comparing categories
        # - One categorical dimension + one numeric measure
        # - Moderate number of categories
        if categorical_cols and numeric_cols and num_rows <= 30:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            return ChartType.BAR, {
                "title": f"{num_col} by {cat_col}",
                "x_axis": cat_col,
                "y_axis": num_col,
                "x_label": cat_col,
                "y_label": num_col,
                "description": f"Comparison of {num_col} across different {cat_col}",
                "horizontal": num_rows > 10  # Use horizontal bars for many categories
            }
        
        # SCATTER PLOT: For correlations between two numeric variables
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            return ChartType.SCATTER, {
                "title": f"{y_col} vs {x_col}",
                "x_axis": x_col,
                "y_axis": y_col,
                "x_label": x_col,
                "y_label": y_col,
                "description": f"Shows relationship between {x_col} and {y_col}"
            }
        
        # TABLE: Fallback for complex data
        return ChartType.TABLE, {
            "title": "Data Table",
            "description": "Data is best displayed in tabular format"
        }
    
    def _format_data_for_chart(
        self,
        query_result: List[Dict[str, Any]],
        column_types: Dict[str, Dict[str, Any]],
        chart_type: ChartType
    ) -> Dict[str, Any]:
        """Format data structure for frontend charting library"""
        
        if chart_type == ChartType.TABLE:
            return {
                "rows": query_result,
                "columns": list(column_types.keys())
            }
        
        # For charts, extract labels and values
        numeric_cols = [c for c, info in column_types.items() if info['is_numeric']]
        categorical_cols = [c for c, info in column_types.items() if info['is_categorical']]
        date_cols = [c for c, info in column_types.items() if info['is_date']]
        
        # Determine label column (x-axis)
        label_col = None
        if categorical_cols:
            label_col = categorical_cols[0]
        elif date_cols:
            label_col = date_cols[0]
        elif column_types:
            # Use first non-numeric column
            label_col = next((c for c, info in column_types.items() if not info['is_numeric']), None)
        
        if not label_col and column_types:
            # If all numeric, use first column as label
            label_col = list(column_types.keys())[0]
        
        # Extract data
        labels = [str(row.get(label_col, '')) for row in query_result] if label_col else []
        
        # Extract datasets (one per numeric column)
        datasets = []
        for num_col in numeric_cols[:3]:  # Limit to 3 datasets for clarity
            values = []
            for row in query_result:
                val = row.get(num_col)
                if val is not None:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        values.append(0)
                else:
                    values.append(0)
            
            datasets.append({
                "label": num_col,
                "data": values
            })
        
        return {
            "labels": labels,
            "datasets": datasets
        }


# Singleton instance
_analyzer_instance = None


def get_visualization_analyzer() -> VisualizationAnalyzer:
    """Get singleton visualization analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = VisualizationAnalyzer()
    return _analyzer_instance
