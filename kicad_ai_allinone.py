#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re, json, argparse, requests, pandas as pd, pdfplumber, yaml, math, cmath
from typing import Dict, Any, List, Optional, Tuple
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

# PySpice (simulation optionnelle)
SIM_AVAILABLE = True
try:
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import u_V, u_Hz
except Exception:
    SIM_AVAILABLE = False

# =========================
# Utilitaires généraux
# =========================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s) if s else ""

def download_file(url: str, out_dir: str, filename_hint: str, exts: Tuple[str, ...]) -> Optional[str]:
    if not url: return None
    ensure_dir(out_dir)
    try:
        resp = requests.get(url, timeout=25)
        resp.raise_for_status()
        ext = os.path.splitext(url.split("?")[0])[1].lower()
        if ext not in exts:
            ctype = resp.headers.get("content-type", "").lower()
            if "pdf" in ctype: ext = ".pdf"
            elif "text" in ctype or "spice" in ctype: ext = ".lib"
            else: ext = exts[0]
        fname = os.path.join(out_dir, f"{sanitize(filename_hint) or 'file'}{ext}")
        with open(fname, "wb") as f:
            f.write(resp.content)
        return fname
    except Exception as e:
        print(f"[WARN] Download failed ({url}): {e}")
        return None

# =========================
# Lecture BOM et Netlist
# =========================

def read_bom(bom_path: str) -> pd.DataFrame:
    ext = os.path.splitext(bom_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(bom_path)
    elif ext == ".xml":
        tree = etree.parse(bom_path)
        root = tree.getroot()
        rows = []
        for c in root.findall(".//row") + root.findall(".//item") + root.findall(".//component"):
            row = {k: (c.get(k) or "") for k in c.keys()}
            for tag in ["mpn","manufacturer","value","ref","qty","datasheet","spice_model_url"]:
                el = c.find(tag)
                if el is not None and el.text:
                    row[tag] = el.text
            rows.append(row)
        df = pd.DataFrame(rows)
    else:
        raise ValueError("Unsupported BOM format (CSV or XML expected).")
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ("ref","value","mpn","qty","datasheet","spice_model_url"):
        if col not in df.columns: df[col] = ""
    try:
        df["qty"] = df["qty"].fillna(1).astype(int)
    except:
        df["qty"] = 1
    return df.fillna("")

def read_netlist(netlist_path: str) -> Dict[str, Any]:
    tree = etree.parse(netlist_path)
    root = tree.getroot()
    comps = []
    nets = []
    
    # Find components
    for c in root.findall(".//comp"):
        ref = c.get("ref") or ""
        value = c.findtext("value") or ""
        fp = c.findtext("footprint") or ""
        comps.append({"ref": ref, "value": value, "footprint": fp})
    
    # Find nets
    for n in root.findall(".//net"):
        nets.append({
            "name": n.get("name"),
            "nodes": [{"ref": node.get("ref"), "pin": node.get("pin")} for node in n.findall("node")]
        })
    return {"components": comps, "nets": nets}

# =========================
# APIs Octopart et Mouser
# =========================

def fetch_from_octopart(mpn: str, api_key: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not api_key or not mpn:
        return None, None
    # Placeholder REST
    try:
        url = "https://octopart.com/api/v4/endpoint"
        r = requests.get(url, params={"mpn": mpn, "apikey": api_key}, timeout=12)
        if r.status_code == 200:
            data = r.json()
            ds_url = None
            spice_url = None
            if isinstance(data, dict):
                if "datasheets" in data and data["datasheets"]:
                    first = data["datasheets"][0]
                    ds_url = first.get("url") or first.get("link") or ds_url
                for key in ["cad_models","simulation_models","models","files"]:
                    if key in data:
                        for item in data[key] or []:
                            t = (item.get("type") or "").lower()
                            if any(x in t for x in ["spice","pspice","ltspice"]):
                                spice_url = item.get("url") or item.get("download_url")
                                break
            return ds_url, spice_url
    except Exception as e:
        print(f"[WARN] Octopart (endpoint placeholder) {mpn}: {e}")
    # GraphQL fallback
    try:
        gql_url = "https://octopart.com/api/v4/graph"
        query = """
        query ($mpn: String!) {
          parts(mpn: $mpn) {
            datasheets { url }
            models { url type }
          }
        }
        """
        headers = {"Content-Type": "application/json", "X-API-KEY": api_key}
        r = requests.post(gql_url, json={"query": query, "variables": {"mpn": mpn}}, headers=headers, timeout=12)
        if r.status_code == 200:
            obj = r.json()
            parts = (obj.get("data", {}) or {}).get("parts", []) or []
            ds_url = None
            spice_url = None
            if parts:
                ds = parts[0].get("datasheets") or []
                if ds: ds_url = ds[0].get("url")
                mods = parts[0].get("models") or []
                for m in mods:
                    if "spice" in (m.get("type","").lower()):
                        spice_url = m.get("url")
                        break
            return ds_url, spice_url
    except Exception as e:
        print(f"[WARN] Octopart (GraphQL) {mpn}: {e}")
    return None, None

def fetch_from_mouser(mpn: str, api_key: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not api_key or not mpn:
        return None, None
    try:
        url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
        payload = {"SearchByPartRequest": {"mouserPartNumber": mpn}}
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            items = (data.get("SearchResults", {}) or {}).get("Parts", []) or []
            if items:
                ds_url = items[0].get("DataSheetUrl")
                return ds_url, None
    except Exception as e:
        print(f"[WARN] Mouser fetch fail {mpn}: {e}")
    return None, None

# =========================
# Extraction SOA depuis datasheet
# =========================

SOA_PATTERNS = [
    ("Vds_max", r"(?:Vds|Drain[-\s]?Source\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V"),
    ("Id_max",  r"(?:Id|Drain\s*Current)[^\n]*?(\d+\.?\d*)\s*A"),
    ("Pd_max",  r"(?:P[dD]|Power\s*Dissipation)[^\n]*?(\d+\.?\d*)\s*W"),
    ("Vr_max",  r"(?:Vr|Reverse\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V"),
    ("If_max",  r"(?:If|Forward\s*Current)[^\n]*?(\d+\.?\d*)\s*A"),
]

def extract_soa_from_pdf_file(pdf_path: str) -> Dict[str, float]:
    if not pdf_path or not os.path.exists(pdf_path):
        return {}
    out: Dict[str, float] = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages
            prioritized = []
            others = []
            for p in pages:
                text = (p.extract_text() or "")
                if any(k in text for k in ["Absolute Maximum Ratings", "Safe Operating Area", "Maximum Ratings"]):
                    prioritized.append(text)
                else:
                    others.append(text)
            for text in prioritized + others:
                for key, pat in SOA_PATTERNS:
                    if key in out: continue
                    m = re.search(pat, text, flags=re.IGNORECASE)
                    if m:
                        try: out[key] = float(m.group(1))
                        except: pass
                if len(out) >= 3:
                    break
    except Exception as e:
        print(f"[WARN] SOA parse fail {pdf_path}: {e}")
    return out

# =========================
# Vérification SOA
# =========================

def check_soa(soa: Dict[str, float], cond: Dict[str, float]) -> List[str]:
    alerts = []
    if not (soa or cond):
        return alerts
    def verdict(meas, limit, label):
        if meas is None or limit is None: return None
        if meas > limit: return f"❌ {label}={meas} > {limit} (limit)"
        if meas > 0.8*limit: return f"⚠ {label}={meas} close to limit {limit}"
        return f"✅ {label}={meas} OK (limit {limit})"
    pairs = [
        ("Vds", cond.get("Vds_max"), soa.get("Vds_max")),
        ("Id",  cond.get("Id_max"),  soa.get("Id_max")),
        ("Pd",  cond.get("Pd_max"),  soa.get("Pd_max")),
        ("Vr",  cond.get("Vr_max"),  soa.get("Vr_max")),
        ("If",  cond.get("If_max"),  soa.get("If_max")),
    ]
    for label, meas, limit in pairs:
        v = verdict(meas, limit, label)
        if v: alerts.append(v)
    return alerts

# =========================
# Enrichissement BOM via APIs + téléchargements
# =========================

def enrich_bom_with_sources(df: pd.DataFrame,
                            octopart_key: Optional[str],
                            mouser_key: Optional[str]) -> pd.DataFrame:
    for col in ("datasheet","spice_model_url","datasheet_path","spice_model_path","soa_json"):
        if col not in df.columns: df[col] = ""
    ensure_dir("datasheets")
    ensure_dir("models")

    for i, row in df.iterrows():
        ref = str(row.get("ref","")).strip()
        mpn = str(row.get("mpn","")).strip()
        ds = str(row.get("datasheet","")).strip()
        spice = str(row.get("spice_model_url","")).strip()

        # Requête API si manquant
        if (not ds or not spice) and mpn:
            ds_octo, sp_octo = fetch_from_octopart(mpn, octopart_key)
            ds = ds or ds_octo
            spice = spice or sp_octo
            if not ds and mouser_key:
                ds_m, sp_m = fetch_from_mouser(mpn, mouser_key)
                ds = ds or ds_m
                spice = spice or sp_m

        # Télécharger datasheet
        ds_path = row.get("datasheet_path","")
        if ds and not ds_path:
            ds_path = download_file(ds, "datasheets", mpn or ref, (".pdf",))
            if ds_path: 
                df.loc[i, "datasheet_path"] = ds_path
            df.loc[i, "datasheet"] = ds

        # Télécharger modèle SPICE
        sp_path = row.get("spice_model_path","")
        if spice and not sp_path:
            sp_path = download_file(spice, "models", mpn or ref, (".lib",".sub",".cir",".mod",".txt"))
            if sp_path: 
                df.loc[i, "spice_model_path"] = sp_path
            df.loc[i, "spice_model_url"] = spice

        # Extraire SOA si datasheet locale dispo
        if df.loc[i, "datasheet_path"] and not row.get("soa_json",""):
            soa = extract_soa_from_pdf_file(df.loc[i, "datasheet_path"])
            if soa:
                df.loc[i, "soa_json"] = json.dumps(soa)

    return df

# =========================
# Conditions d'exploitation
# =========================

def load_operating_conditions(path: Optional[str]) -> Dict[str, Dict[str, float]]:
    if not path: return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    out: Dict[str, Dict[str, float]] = {}
    for ref, d in (data.items() if isinstance(data, dict) else []):
        try:
            out[str(ref)] = {k: float(v) for k, v in (d or {}).items()}
        except:
            out[str(ref)] = d or {}
    return out

# =========================
# Simulation ngspice (AC/Bode simple)
# =========================

def run_bode_from_spice(spice_netlist_path: str,
                        in_node: str = "in",
                        out_node: str = "out",
                        start_hz: float = 1.0,
                        stop_hz: float = 1e6,
                        points_per_dec: int = 50) -> Dict[str, Any]:
    if not SIM_AVAILABLE:
        return {"available": False, "note": "PySpice/ngspice not available."}
    try:
        # Inclure le netlist SPICE exporté
        circuit = Circuit("Imported")
        circuit.include(spice_netlist_path)
        # Ajout d'une source AC si nécessaire (si déjà présente, ngspice s'en sortira)
        # Ici on ne force pas, on se contente de mesurer V(out)/V(in)
        sim = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = sim.ac(start_frequency=start_hz@u_Hz,
                          stop_frequency=stop_hz@u_Hz,
                          number_of_points=points_per_dec,
                          variation='dec')
        freqs = [float(f) for f in analysis.frequency]
        if out_node not in analysis.nodes or in_node not in analysis.nodes:
            return {"available": True, "note": "Nodes 'in' or 'out' not found. Rename your nodes, or adapt parameters.", "points": []}
        vout = analysis.nodes[out_node]
        vin = analysis.nodes[in_node]
        gains_db = []
        phases_deg = []
        for i, f in enumerate(freqs):
            try:
                h = complex(vout[i]) / complex(vin[i])
                gains_db.append(20.0 * math.log10(abs(h) + 1e-18))
                phases_deg.append(math.degrees(cmath.phase(h)))
            except Exception:
                gains_db.append(float("nan"))
                phases_deg.append(float("nan"))
        # estimer fc (gain 0 dB) et marge de phase (phase à fc)
        fc = None
        pm = None
        for i in range(1, len(freqs)):
            if gains_db[i-1] > 0 and gains_db[i] <= 0:
                fc = freqs[i]
                pm = phases_deg[i]
                break
        return {
            "available": True,
            "note": "Bode calculated on ratio V(out)/V(in).",
            "fc": fc,
            "phase_margin_deg": pm,
            "sample": list(zip(freqs[:10], gains_db[:10], phases_deg[:10]))
        }
    except Exception as e:
        return {"available": False, "note": f"Simulation failed: {e}"}

# =========================
# IA Hugging Face
# =========================

from transformers import pipeline

def build_prompt(project_name: str, bom: pd.DataFrame, netlist: Dict[str, Any],
                 ops: Dict[str, Dict[str, float]], bode: Optional[Dict[str, Any]]) -> str:
    preview_cols = [c for c in ["ref","value","mpn","qty","datasheet","spice_model_path"] if c in bom.columns]
    preview = bom[preview_cols].head(60).to_dict(orient="records")
    soa_snips = []
    for _, row in bom.iterrows():
        ref = str(row.get("ref","")).strip()
        if not ref: continue
        sj = row.get("soa_json","")
        if not sj: continue
        try:
            sd = json.loads(sj)
            sn = {k: sd.get(k) for k in ["Vds_max","Id_max","Pd_max","Vr_max","If_max"] if k in sd}
            if sn: soa_snips.append({ref: sn})
        except: pass

    bode_text = ""
    if bode:
        if bode.get("available"):
            bode_text = f"Bode: {bode.get('note')}, fc={bode.get('fc')}, phase_margin_deg={bode.get('phase_margin_deg')}, sample={bode.get('sample')[:5]}"
        else:
            bode_text = f"Bode unavailable: {bode.get('note')}"

    prompt = f"""
You are an expert in electronic engineering. Based on the enriched BOM (datasheets, SPICE models), extracted SOA limits, operating conditions, and Bode simulation summary (if provided), produce a structured, concise and actionable analysis:
- Identify functional stages (power supply, filters, drivers, logic/RF...).
- Check SOA margins (cite refs), polarities, value inconsistencies.
- Propose corrections and alternatives (more robust/efficient components).
- Advise on stability (Bode), digital terminations, decoupling, ground return, EMI/EMC.
- Conclude with 5 priority, measurable actions.

Project: {project_name}
Components: {len(netlist.get('components',[]))}
Nets: {len(netlist.get('nets',[]))}

BOM (preview, 60 max):
{json.dumps(preview, ensure_ascii=False, indent=2)}

Extracted SOA limits (preview):
{json.dumps(soa_snips, ensure_ascii=False, indent=2)}

Operating conditions:
{json.dumps(ops, ensure_ascii=False, indent=2)}

{bode_text}

Respond in Markdown, clear and concise. Cite refs when you report a point.
""".strip()
    return prompt

def run_hf_model(model_id: str, prompt: str, device: str = "cpu") -> str:
    try:
        if "flan" in model_id.lower() or "t5" in model_id.lower():
            nlp = pipeline("text2text-generation", model=model_id, device=-1 if device=="cpu" else 0)
            out = nlp(prompt, max_new_tokens=900, do_sample=False)
            return out[0]["generated_text"]
        else:
            nlp = pipeline("text-generation", model=model_id, device=-1 if device=="cpu" else 0)
            out = nlp(prompt, max_new_tokens=900, do_sample=True, temperature=0.4, top_p=0.9)
            return out[0]["generated_text"]
    except Exception as e:
        return f"AI Error: {e}"

# =========================
# Rapport
# =========================

def make_report(project_name: str,
                bom_df: pd.DataFrame,
                netlist: Dict[str, Any],
                ops: Dict[str, Dict[str, float]],
                bode: Optional[Dict[str, Any]],
                ai_text: str) -> str:
    out = []
    out.append(f"# AI Analysis Report — {project_name}\n")
    out.append("## Summary")
    out.append(f"- **Components:** {len(netlist.get('components', []))}")
    out.append(f"- **Nets:** {len(netlist.get('nets', []))}\n")

    if bode:
        out.append("## Bode Simulation (summary)")
        if bode.get("available"):
            out.append(f"- **Note:** {bode.get('note')}")
            out.append(f"- **Fc:** {bode.get('fc')}")
            out.append(f"- **Phase margin:** {bode.get('phase_margin_deg')}")
            sample = bode.get("sample") or []
            if sample:
                out.append("- **Examples (f, gain dB, phase °):**")
                for f,g,ph in sample:
                    out.append(f"  - {f:.2f} Hz, {g:.2f} dB, {ph:.1f}°")
        else:
            out.append(f"- **Note:** {bode.get('note')}")
        out.append("")

    out.append("## SOA per component")
    for _, row in bom_df.iterrows():
        ref = str(row.get("ref","")).strip()
        if not ref: continue
        mpn = str(row.get("mpn","")).strip()
        ds = str(row.get("datasheet","")).strip()
        ds_path = str(row.get("datasheet_path","")).strip()
        sp_path = str(row.get("spice_model_path","")).strip()
        sj = row.get("soa_json","")
        out.append(f"### {ref} — {mpn}")
        if ds: out.append(f"- **Datasheet:** {ds}")
        if ds_path: out.append(f"- **Local datasheet:** {ds_path}")
        if sp_path: out.append(f"- **SPICE model:** {sp_path}")
        if sj:
            soa = json.loads(sj)
            cond = ops.get(ref, {})
            alerts = check_soa(soa, cond)
            if alerts:
                out.append("- **SOA check:**")
                for a in alerts: out.append(f"  - {a}")
            else:
                out.append("- **SOA check:** insufficient data or no conditions provided.")
        else:
            out.append("- **SOA:** not extracted (no datasheet/parsing failed).")
        out.append("")
    out.append("## AI Analysis")
    out.append(ai_text.strip() if ai_text else "_AI unavailable_")
    return "\n".join(out)

# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(description="KiCad → AI all-in-one: Octopart/Mouser, SOA, SPICE, HF report.")
    parser.add_argument("--netlist", required=True, help="KiCad netlist (.net/.xml)")
    parser.add_argument("--bom", required=True, help="KiCad BOM (.csv/.xml)")
    parser.add_argument("--out", default="rapport.md", help="Output Markdown report")
    parser.add_argument("--hf-model", default="google/flan-t5-large", help="Hugging Face model (ex: mistralai/Mistral-7B-Instruct-v0.2)")
    parser.add_argument("--device", default="cpu", choices=["cpu","cuda"], help="AI inference device")
    parser.add_argument("--operating", default=None, help="YAML file of operating conditions by ref")
    parser.add_argument("--octopart-key", default=None, help="Octopart API key")
    parser.add_argument("--mouser-key", default=None, help="Mouser API key")
    parser.add_argument("--spice-netlist", default=None, help="SPICE netlist file exported from KiCad (.cir/.spice)")
    parser.add_argument("--bode-in-node", default="in", help="Input node name for Bode (default: in)")
    parser.add_argument("--bode-out-node", default="out", help="Output node name for Bode (default: out)")
    args = parser.parse_args()

    project_name = os.path.splitext(os.path.basename(args.netlist))[0]

    print("Reading BOM…")
    bom_df = read_bom(args.bom)

    print("Reading netlist…")
    netlist = read_netlist(args.netlist)

    print("Enriching via Octopart/Mouser + downloads…")
    bom_df = enrich_bom_with_sources(bom_df, args.octopart_key, args.mouser_key)

    print("Loading operating conditions…")
    ops = load_operating_conditions(args.operating)

    bode = None
    if args.spice_netlist:
        print("Bode simulation (ngspice)…")
        bode = run_bode_from_spice(args.spice_netlist, args.bode_in_node, args.bode_out_node)

    print(f"AI inference ({args.hf_model})…")
    prompt = build_prompt(project_name, bom_df, netlist, ops, bode)
    ai_text = run_hf_model(args.hf_model, prompt, device=args.device)

    print("Generating report…")
    report = make_report(project_name, bom_df, netlist, ops, bode, ai_text)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"OK. Report written: {args.out}")

if __name__ == "__main__":
    main()
