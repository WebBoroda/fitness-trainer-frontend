"""Validate editable config, assets and server-rendered SEO metadata."""
from pathlib import Path
import json
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
config_file = root / "assets/js/site-config.js"
original = config_file.read_text(encoding="utf-8")
def build():
    subprocess.run([sys.executable, "tools/build_site.py"], cwd=root, check=True,
                   stdout=subprocess.DEVNULL)
try:
    build()
    generated = (root / "dist/index.html").read_text(encoding="utf-8")
    assert "<title>Fitnes Trener | Персональні та онлайн-тренування</title>" in generated
    assert 'content="noindex,follow"' in generated
    assert "Yuliia Zahorodnia" not in generated
    assert 'assets/images/fitness-trainer-hero.webp' in generated
    assert (root / "dist/assets/images/fitness-trener-favicon.svg").is_file()
    assert (root / "dist/assets/css/site-theme.css").is_file()
    assert len(list((root / "dist/assets/images").iterdir())) == 45
    assert 'schema.org' in generated and '"@type":"WebPage"' in generated
    modified = original.replace('"name": "Fitnes Trener"', '"name": "Олена Тренер"')
    modified = modified.replace('"isPerson": false', '"isPerson": true')
    assert modified != original
    config_file.write_text(modified, encoding="utf-8")
    build()
    person = (root / "dist/index.html").read_text(encoding="utf-8")
    assert "<title>Фітнес-тренер Олена Тренер |" in person
    assert '"@type":"Person"' in person
    assert "ОЛЕНА<span>ТРЕНЕР</span>" in person
finally:
    config_file.write_text(original, encoding="utf-8")
    build()
print("Unified settings + SEO static render OK")
