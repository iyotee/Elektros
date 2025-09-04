# API Reference

## Main Script: `kicad_ai_allinone.py`

### Command Line Interface

```bash
python kicad_ai_allinone.py [OPTIONS]
```

#### Required Arguments

- `--netlist NETLIST`: Path to KiCad netlist file (.net or .xml)
- `--bom BOM`: Path to KiCad BOM file (.csv or .xml)

#### Optional Arguments

- `--out OUTPUT`: Output report file path (default: `rapport.md`)
- `--hf-model MODEL`: Hugging Face model ID (default: `google/flan-t5-large`)
- `--device DEVICE`: AI inference device - `cpu` or `cuda` (default: `cpu`)
- `--operating CONDITIONS`: Path to operating conditions YAML file
- `--octopart-key KEY`: Octopart API key
- `--mouser-key KEY`: Mouser API key
- `--spice-netlist NETLIST`: Path to SPICE netlist file for simulation
- `--bode-in-node NODE`: Input node name for Bode analysis (default: `in`)
- `--bode-out-node NODE`: Output node name for Bode analysis (default: `out`)

## Utility Modules

### `utils.api_clients.py`

#### `OctopartClient`

```python
class OctopartClient:
    def __init__(self, api_key: Optional[str] = None)
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]
```

**Methods:**
- `search_part(mpn)`: Search for part by MPN, returns (datasheet_url, spice_model_url)

#### `MouserClient`

```python
class MouserClient:
    def __init__(self, api_key: Optional[str] = None)
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]
```

**Methods:**
- `search_part(mpn)`: Search for part by MPN, returns (datasheet_url, spice_model_url)

#### `APIManager`

```python
class APIManager:
    def __init__(self, octopart_key: Optional[str] = None, mouser_key: Optional[str] = None)
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]
```

**Methods:**
- `search_part(mpn)`: Search using available APIs, returns (datasheet_url, spice_model_url)

### `utils.soa_extractor.py`

#### `SOAPattern`

```python
class SOAPattern:
    def __init__(self, name: str, pattern: str, unit: str, description: str = "")
    def extract(self, text: str) -> Optional[float]
```

**Methods:**
- `extract(text)`: Extract value from text using the pattern

#### `SOAExtractor`

```python
class SOAExtractor:
    def __init__(self)
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, float]
    def extract_from_text(self, text: str) -> Dict[str, float]
    def validate_soa(self, soa: Dict[str, float]) -> List[str]
```

**Methods:**
- `extract_from_pdf(pdf_path)`: Extract SOA parameters from PDF file
- `extract_from_text(text)`: Extract SOA parameters from text
- `validate_soa(soa)`: Validate extracted SOA parameters

#### `SOAChecker`

```python
class SOAChecker:
    def __init__(self, safety_margin: float = 0.8)
    def check_compliance(self, soa: Dict[str, float], operating_conditions: Dict[str, float]) -> List[str]
```

**Methods:**
- `check_compliance(soa, operating_conditions)`: Check SOA compliance against operating conditions

### `utils.spice_simulator.py`

#### `BodeAnalyzer`

```python
class BodeAnalyzer:
    def __init__(self)
    def analyze_netlist(self, netlist_path: str, input_node: str = "in", output_node: str = "out", start_freq: float = 1.0, stop_freq: float = 1e6, points_per_decade: int = 50) -> Dict[str, Any]
```

**Methods:**
- `analyze_netlist(...)`: Perform Bode analysis on SPICE netlist

#### `SpiceNetlistParser`

```python
class SpiceNetlistParser:
    def __init__(self)
    def parse_file(self, filepath: str) -> Dict[str, Any]
    def parse_content(self, content: str) -> Dict[str, Any]
```

**Methods:**
- `parse_file(filepath)`: Parse SPICE netlist file
- `parse_content(content)`: Parse SPICE netlist content

#### `StabilityAnalyzer`

```python
class StabilityAnalyzer:
    def __init__(self)
    def analyze_stability(self, frequencies: List[float], gains_db: List[float], phases_deg: List[float]) -> Dict[str, Any]
```

**Methods:**
- `analyze_stability(...)`: Analyze circuit stability from Bode data

### `utils.ai_analyzer.py`

#### `AIAnalyzer`

```python
class AIAnalyzer:
    def __init__(self, model_id: str = "google/flan-t5-large", device: str = "cpu")
    def analyze_circuit(self, project_name: str, bom_df: pd.DataFrame, netlist: Dict[str, Any], operating_conditions: Dict[str, Dict[str, float]], bode_data: Optional[Dict[str, Any]] = None) -> str
```

**Methods:**
- `analyze_circuit(...)`: Perform AI analysis of the circuit

#### `ReportGenerator`

```python
class ReportGenerator:
    def __init__(self)
    def generate_report(self, project_name: str, bom_df: pd.DataFrame, netlist: Dict[str, Any], operating_conditions: Dict[str, Dict[str, float]], bode_data: Optional[Dict[str, Any]], ai_analysis: str) -> str
```

**Methods:**
- `generate_report(...)`: Generate comprehensive report

## Data Structures

### BOM DataFrame

The BOM DataFrame should contain the following columns:

- `ref`: Component reference (e.g., "R1", "C1", "U1")
- `value`: Component value (e.g., "10k", "100nF", "LM358")
- `mpn`: Manufacturer Part Number
- `manufacturer`: Manufacturer name
- `qty`: Quantity
- `datasheet`: Datasheet URL
- `spice_model_url`: SPICE model URL
- `datasheet_path`: Local datasheet file path
- `spice_model_path`: Local SPICE model file path
- `soa_json`: Extracted SOA data as JSON string

### Netlist Structure

```python
{
    "components": [
        {
            "ref": "R1",
            "value": "10k",
            "footprint": "Resistor_SMD:R_0603_1608Metric"
        }
    ],
    "nets": [
        {
            "name": "VCC",
            "nodes": [
                {"ref": "R1", "pin": "1"},
                {"ref": "C1", "pin": "1"}
            ]
        }
    ]
}
```

### Operating Conditions Structure

```python
{
    "Q1": {
        "Vds_max": 48.0,
        "Id_max": 10.0,
        "Pd_max": 5.0
    },
    "D3": {
        "Vr_max": 60.0,
        "If_max": 2.0
    }
}
```

### Bode Analysis Results

```python
{
    "available": True,
    "note": "Bode analysis completed successfully",
    "frequencies": [1.0, 10.0, 100.0, ...],
    "gains_db": [0.0, -3.0, -20.0, ...],
    "phases_deg": [0.0, -45.0, -90.0, ...],
    "crossover_freq": 1000.0,
    "phase_margin": 45.0,
    "sample": [(1.0, 0.0, 0.0), (10.0, -3.0, -45.0), ...]
}
```

## Error Handling

All modules include comprehensive error handling:

- **API Errors**: Network timeouts, rate limits, authentication failures
- **File Errors**: Missing files, permission issues, format errors
- **Simulation Errors**: Invalid netlists, missing nodes, convergence issues
- **AI Errors**: Model loading failures, generation errors, memory issues

## Configuration

### Environment Variables

- `OCTOPART_API_KEY`: Octopart API key
- `MOUSER_API_KEY`: Mouser API key
- `CUDA_VISIBLE_DEVICES`: GPU device selection for CUDA

### Configuration File (`config.yaml`)

```yaml
api_keys:
  octopart: null
  mouser: null

ai:
  default_model: "google/flan-t5-large"
  device: "cpu"
  max_tokens: 900
  temperature: 0.4
  top_p: 0.9

simulation:
  bode:
    start_frequency_hz: 1.0
    stop_frequency_hz: 1000000.0
    points_per_decade: 50
    input_node: "in"
    output_node: "out"

paths:
  datasheets_dir: "datasheets"
  models_dir: "models"
  reports_dir: "reports"
```

## Examples

### Basic Usage

```python
from kicad_ai_allinone import main
import sys

sys.argv = [
    'kicad_ai_allinone.py',
    '--netlist', 'project.net',
    '--bom', 'BOM.csv',
    '--out', 'report.md'
]
main()
```

### Using Utility Modules

```python
from utils.api_clients import APIManager
from utils.soa_extractor import SOAExtractor
from utils.spice_simulator import BodeAnalyzer
from utils.ai_analyzer import AIAnalyzer

# API client
api_manager = APIManager(octopart_key="your_key", mouser_key="your_key")
datasheet_url, spice_url = api_manager.search_part("IRF540N")

# SOA extraction
soa_extractor = SOAExtractor()
soa_data = soa_extractor.extract_from_pdf("datasheet.pdf")

# SPICE simulation
bode_analyzer = BodeAnalyzer()
results = bode_analyzer.analyze_netlist("circuit.cir")

# AI analysis
ai_analyzer = AIAnalyzer("google/flan-t5-large", "cpu")
analysis = ai_analyzer.analyze_circuit("My Project", bom_df, netlist, operating_conditions, bode_data)
```
