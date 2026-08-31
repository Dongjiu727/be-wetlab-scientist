# 🔬 Be a WetLab Scientist

An interactive troubleshooting assistant that turns over a decade of hands-on Western Blot / qPCR debugging experience into a structured diagnostic tool for lab students and postdocs. Currently focused on tumor-immunology wet-lab workflows, with more assay types planned.

## Why this project

Most existing resources (vendor troubleshooting guides, teaching-simulation websites) are static symptom-cause tables — not grounded in real experimental cases, and not built for interactive differential diagnosis. This project is different:

- **Built from real cases** — every diagnostic path is grounded in problems actually encountered and verified in the lab, not hypothetical scenarios.
- **An interactive decision graph, not a flat table** — symptom → rule out known info → differentiating questions → confirmatory experiment, narrowing step by step.
- **Reusable diagnostic subtrees** — common checks (e.g. antibody validation, primer verification) are defined once and reused across multiple symptoms, so the knowledge base doesn't bloat as cases are added.
- **Two entry points at the same level** — "Something went wrong" (interactive diagnosis) and "Planning a new experiment" (preventive best-practice guides) — covering the full experiment lifecycle, not just firefighting.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

## Project structure

```
engine/               # Assay-agnostic diagnostic engine — loads and traverses the decision graph
app/                  # Streamlit interactive interface
knowledge_base/
  western_blot/        # WB shared nodes + case library
  qpcr/                 # qPCR shared nodes + case library
  design_guides/       # Preventive experiment-design guides (scaffold, actively growing)
docs/                  # Architecture and design documentation
```

## Current status

- ✅ Western Blot: 2 cases (no signal, weak signal)
- ✅ qPCR: 3 cases (late Ct, no amplification, multiple melt peaks / contamination)
- 🚧 Design guides: scaffold in place, content being filled in
- 🚧 More symptom types coming (high background, aberrant bands, loading-control issues, etc.)

## Contributing

Fellow lab scientists are welcome to contribute additional cases — please see [CONTRIBUTING.md](./CONTRIBUTING.md) first.

## Disclaimer

This tool is compiled from personal lab experience and is intended for educational reference. It is not a substitute for professional guidance — please consult your PI/colleagues and use your judgment for actual experimental decisions.
