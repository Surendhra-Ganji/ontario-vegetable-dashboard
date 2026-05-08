import pytest
import json
from pathlib import Path
import tempfile
import pandas as pd

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with a mock vegetables.json"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_dir.mkdir()
        config_path = config_dir / "vegetables.json"
        sample_data = [
            {
                "id": "test_cabbage",
                "name": "Test Cabbage",
                "display_name": "Cabbage",
                "category": "vegetables",
                "metric_family": "yield_production",
                "dataset_slug": "test-cabbage-data"
            },
            {
                "id": "test_tomato",
                "name": "Test Tomato",
                "display_name": "Tomato",
                "category": "vegetables",
                "metric_family": "yield_production",
                "dataset_slug": "test-tomato-data"
            }
        ]
        with open(config_path, 'w') as f:
            json.dump(sample_data, f)
        yield tmpdir

@pytest.fixture
def temp_processed_dir(temp_config_dir):
    """Create a temporary processed data directory with sample CSV"""
    processed_dir = Path(temp_config_dir) / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create sample CSV data
    sample_df = pd.DataFrame({
        'Year': [2020, 2021, 2022],
        "Marketed Production ('000 lbs)": [1000, 1100, 1200],
        "Average Price (cents/lb)": [50, 55, 60],
        "Average Yield (lbs/acre)": [20000, 21000, 22000],
        "Farm Value ($'000)": [500, 605, 720],
        "Harvested Area (acres)": [50, 52, 55]
    })
    
    csv_path = processed_dir / "test_cabbage.csv"
    sample_df.to_csv(csv_path, index=False)
    
    yield processed_dir