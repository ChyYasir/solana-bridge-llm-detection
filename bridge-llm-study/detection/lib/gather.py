import json
from pathlib import Path

SOURCE_FILES = ["lib.rs", "error.rs", "state.rs", "instruction.rs", "pda.rs", "ed25519.rs", "processor.rs"]


def read_program_source(program_dir: Path) -> str:
    parts = []
    for name in SOURCE_FILES:
        path = program_dir / "src" / name
        if path.exists():
            parts.append(f"// === {name} ===\n{path.read_text()}")
    return "\n\n".join(parts)


def read_trace(trace_path: Path) -> dict:
    """Load a captured trace and strip anything that gives away the ground-truth
    answer — not just the exploit script's own "outcome" verdict, but also the
    narrative step names we wrote for our own debugging convenience (e.g. "strike:
    lock (fake mint)"), which describe intent a real observer would never see. The
    model should only see what's genuinely on-chain: program logs, signatures,
    errors, balances — not our own labels for what we were testing."""
    data = json.loads(trace_path.read_text())
    data.pop("outcome", None)
    for i, step in enumerate(data.get("steps", [])):
        step["name"] = f"step {i + 1}"
    return data
