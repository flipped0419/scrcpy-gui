from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "src/App.tsx"
text = path.read_text(encoding="utf-8")
old = "    theme,\n    setTheme,\n    colorMode,"
new = "    colorMode,"
if old not in text:
    raise RuntimeError("Could not find theme bindings in App.tsx")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Light UI cleanup applied successfully.")
