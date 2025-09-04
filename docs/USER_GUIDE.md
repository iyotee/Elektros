# User Guide

## Getting Started

### Quick Start

1. **Install the tool:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with example data:**
   ```bash
   python kicad_ai_allinone.py \
     --netlist examples/sample_netlist.xml \
     --bom examples/sample_bom.csv \
     --operating examples/operating_conditions.yaml \
     --out my_first_report.md
   ```

3. **View the report:**
   ```bash
   cat my_first_report.md
   ```

### With Your Own KiCad Project

1. **Export from KiCad:**
   - Open your project in KiCad
   - Go to File → Export → Netlist
   - Choose XML format and save as `project.net`
   - Go to Tools → Generate Bill of Materials
   - Choose CSV format and save as `BOM.csv`

2. **Create operating conditions file:**
   ```yaml
   # operating_conditions.yaml
   Q1:
     Vds_max: 48.0
     Id_max: 10.0
     Pd_max: 5.0
   ```

3. **Run analysis:**
   ```bash
   python kicad_ai_allinone.py \
     --netlist project.net \
     --bom BOM.csv \
     --operating operating_conditions.yaml \
     --out analysis_report.md
   ```

## Step-by-Step Tutorial

### Step 1: Prepare Your KiCad Project

1. **Complete your schematic** in KiCad Eeschema
2. **Assign footprints** to all components
3. **Add component values** (resistance, capacitance, etc.)
4. **Add manufacturer part numbers** (MPN) where possible

### Step 2: Export Required Files

#### Export Netlist
1. In Eeschema, go to **Tools → Generate Netlist**
2. Choose **Netlist format: KiCad**
3. Click **Generate Netlist**
4. Save as `project.net`

#### Export BOM
1. In Eeschema, go to **Tools → Generate Bill of Materials**
2. Choose **CSV format**
3. Click **Generate**
4. Save as `BOM.csv`

#### Export SPICE Netlist (Optional)
1. In Eeschema, go to **File → Export → Netlist**
2. Choose **SPICE format**
3. Save as `project.cir`

### Step 3: Create Operating Conditions

Create a YAML file defining expected operating conditions:

```yaml
# operating_conditions.yaml

# Power MOSFET
Q1:
  Vds_max: 48.0    # Maximum drain-source voltage
  Id_max: 10.0     # Maximum drain current
  Pd_max: 5.0      # Maximum power dissipation

# Diode
D1:
  Vr_max: 60.0     # Maximum reverse voltage
  If_max: 2.0      # Maximum forward current

# Voltage Regulator
U1:
  Vout_target: 5.0 # Target output voltage
  Iout_max: 1.0    # Maximum output current

# Resistor
R1:
  P_max: 0.25      # Maximum power rating
  V_max: 50.0      # Maximum voltage

# Capacitor
C1:
  V_max: 25.0      # Maximum voltage rating
  I_ripple_max: 0.1 # Maximum ripple current
```

### Step 4: Set Up API Keys (Optional but Recommended)

#### Get Octopart API Key
1. Go to [Octopart API](https://octopart.com/api)
2. Sign up for a free account
3. Get your API key from the dashboard

#### Get Mouser API Key
1. Go to [Mouser API](https://www.mouser.com/api-hub/)
2. Sign up for a free account
3. Get your API key from the API Hub

#### Set Environment Variables
```bash
# Windows
set OCTOPART_API_KEY=your_octopart_key
set MOUSER_API_KEY=your_mouser_key

# Linux/Mac
export OCTOPART_API_KEY=your_octopart_key
export MOUSER_API_KEY=your_mouser_key
```

### Step 5: Run the Analysis

#### Basic Analysis
```bash
python kicad_ai_allinone.py \
  --netlist project.net \
  --bom BOM.csv \
  --operating operating_conditions.yaml \
  --out report.md
```

#### Full Analysis with APIs and Simulation
```bash
python kicad_ai_allinone.py \
  --netlist project.net \
  --bom BOM.csv \
  --operating operating_conditions.yaml \
  --octopart-key YOUR_OCTOPART_KEY \
  --mouser-key YOUR_MOUSER_KEY \
  --spice-netlist project.cir \
  --out comprehensive_report.md
```

#### Advanced Analysis with Custom AI Model
```bash
python kicad_ai_allinone.py \
  --netlist project.net \
  --bom BOM.csv \
  --operating operating_conditions.yaml \
  --hf-model mistralai/Mistral-7B-Instruct-v0.2 \
  --device cuda \
  --octopart-key YOUR_OCTOPART_KEY \
  --mouser-key YOUR_MOUSER_KEY \
  --spice-netlist project.cir \
  --out advanced_report.md
```

### Step 6: Interpret the Results

The generated report will contain:

1. **Executive Summary**: Key findings and metrics
2. **Circuit Overview**: Component breakdown
3. **SOA Analysis**: Safety compliance checking
4. **Simulation Results**: Bode analysis and stability
5. **AI Engineering Analysis**: Comprehensive technical review
6. **Recommendations**: Actionable improvement suggestions

## Understanding the Output

### SOA Analysis Section

```
### Q1 — IRF540N
- **Datasheet:** https://example.com/datasheet.pdf
- **Local datasheet:** datasheets/IRF540N.pdf
- **SPICE model:** models/IRF540N.lib
- **SOA check:**
  - ✅ Vds=24.0 OK (limit 55.0)
  - ✅ Id=5.0 OK (limit 33.0)
  - ⚠️ Pd=2.5 close to limit 3.0
```

**Interpretation:**
- ✅ Green checkmark: Within safe limits
- ⚠️ Yellow warning: Close to limits (within 80% of maximum)
- ❌ Red X: Exceeds limits (unsafe)

### Simulation Results Section

```
## Simulation Results
### Bode Analysis Results
- **Crossover Frequency:** 1000.00 Hz
- **Phase Margin:** 45.0°
- **Stability:** Good
```

**Interpretation:**
- **Crossover Frequency**: Where gain crosses 0 dB
- **Phase Margin**: Stability margin (45°+ is good)
- **Stability Grade**: Excellent (>60°), Good (45-60°), Marginal (30-45°), Poor (<30°)

### AI Analysis Section

The AI provides:
- **Functional Analysis**: Identifies main circuit blocks
- **Safety & Reliability**: Reviews SOA compliance
- **Performance Analysis**: Evaluates frequency response
- **Design Recommendations**: Suggests improvements
- **Action Items**: Priority tasks with specific recommendations

## Troubleshooting

### Common Issues

#### "No SOA data available"
- **Cause**: No datasheets downloaded or SOA extraction failed
- **Solution**: Check API keys, ensure MPNs are correct, verify PDFs are readable

#### "Simulation unavailable"
- **Cause**: PySpice not installed or invalid netlist
- **Solution**: Install PySpice, check SPICE netlist syntax

#### "AI analysis failed"
- **Cause**: Model not loaded or generation error
- **Solution**: Check internet connection, try smaller model, use CPU mode

#### "API rate limit exceeded"
- **Cause**: Too many API requests
- **Solution**: Wait for rate limit reset, use fewer components, get premium API access

### Debug Mode

Enable verbose output:
```bash
python kicad_ai_allinone.py --netlist project.net --bom BOM.csv --verbose
```

### Check Dependencies

Verify all dependencies are installed:
```bash
python -c "import pandas, lxml, requests, pdfplumber, yaml, transformers, PySpice; print('All dependencies OK')"
```

## Best Practices

### For Accurate SOA Analysis

1. **Use complete MPNs**: Include manufacturer and full part number
2. **Provide realistic operating conditions**: Don't underestimate actual usage
3. **Include safety margins**: Account for temperature and aging effects
4. **Verify datasheet quality**: Ensure PDFs are readable and complete

### For Better AI Analysis

1. **Use descriptive component values**: Include units and tolerances
2. **Provide context in operating conditions**: Explain the application
3. **Include design goals**: What is the circuit supposed to do?
4. **Use appropriate AI model**: Larger models for complex circuits

### For Reliable Simulation

1. **Check SPICE netlist**: Ensure all components have models
2. **Define input/output nodes**: Use clear, consistent naming
3. **Include proper sources**: AC sources for frequency analysis
4. **Verify convergence**: Check for simulation errors

## Advanced Usage

### Custom SOA Patterns

Add custom patterns for specific components:

```python
from utils.soa_extractor import SOAExtractor, SOAPattern

extractor = SOAExtractor()
extractor.patterns.append(
    SOAPattern(
        "Vgs_max",
        r"(?:Vgs|Gate[-\s]?Source\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V",
        "V",
        "Maximum gate-source voltage"
    )
)
```

### Custom AI Prompts

Modify the AI analysis prompt:

```python
from utils.ai_analyzer import AIAnalyzer

analyzer = AIAnalyzer()
# Override the prompt building method
analyzer._build_analysis_prompt = custom_prompt_builder
```

### Batch Processing

Process multiple projects:

```bash
#!/bin/bash
for project in projects/*/; do
    python kicad_ai_allinone.py \
      --netlist "$project/project.net" \
      --bom "$project/BOM.csv" \
      --operating "$project/operating_conditions.yaml" \
      --out "$project/analysis_report.md"
done
```

## Performance Optimization

### For Large Projects

1. **Use GPU for AI**: `--device cuda` (if available)
2. **Process in batches**: Analyze components in groups
3. **Cache downloads**: Reuse downloaded datasheets
4. **Use smaller models**: For faster analysis

### For Memory Constraints

1. **Use CPU mode**: `--device cpu`
2. **Process fewer components**: Filter BOM before analysis
3. **Use smaller AI models**: `google/flan-t5-base`
4. **Disable simulation**: Skip `--spice-netlist` if not needed

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Circuit Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run analysis
        run: |
          python kicad_ai_allinone.py \
            --netlist project.net \
            --bom BOM.csv \
            --operating operating_conditions.yaml \
            --out analysis_report.md
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: analysis-report
          path: analysis_report.md
```

## Support and Community

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the docs/ directory
- **Examples**: See the examples/ directory
- **Discussions**: Join the community discussions

---

**Happy analyzing! 🚀**
