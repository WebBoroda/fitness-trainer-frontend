"""Static integrity tests; do not substitute for live WordPress/visual QA."""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((root / "inc" / "sections.json").read_text(encoding="utf-8"))
json.loads((root / "theme.json").read_text(encoding="utf-8"))
json.loads((root / "blocks" / "landing-section" / "block.json").read_text(encoding="utf-8"))
expected = ["hero", "mission", "formats", "studio", "about", "nutrition", "results", "reviews", "pricing", "faq", "final"]
assert list(data) == expected, f"Unexpected sections: {list(data)}"
assert (root / "style.css").exists()
assert (root / "functions.php").exists()
for name, info in data.items():
    template_path = root / "sections" / f"{name}.php"
    template = template_path.read_text(encoding="utf-8")
    assert "<section" in template and "</section>" in template, name
    assert "data:image/" not in template, f"Unoptimized embedded media in {name}"
    assert "example.invalid" not in template, f"Invalid example link in {name}"
    for image in info["images"]:
        assert (root / image["default"]).is_file(), f"Missing {image['default']}"
    for field_group, variable in (("texts", "t"), ("images", "i"), ("links", "l")):
        keys = [field["key"] for field in info[field_group]]
        assert len(keys) == len(set(keys)), (name, field_group)
        assert all(re.fullmatch(rf"{variable}\\d+", key) for key in keys), (name, keys)
        for key in keys:
            assert f"'{key}'" in template, (name, key)
print(f"PASS: {len(data)} sections, all referenced media, block config and JSON.")
