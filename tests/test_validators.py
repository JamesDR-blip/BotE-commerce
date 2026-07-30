import pandas as pd
from pathlib import Path
from rule_engine.loader import RuleLoader
from validators.fashion import FashionValidator

def test_fashion_autofix_and_validate() -> None:
    frame = pd.DataFrame({"Size": [" s "], "Color": [" red "], "Price": ["100"]})
    fixed = FashionValidator().autofix(frame)
    assert fixed.loc[0, "Size"] == "S"
    rules, _ = RuleLoader(Path("rules_library.yaml")).get("Fashion")
    assert FashionValidator().validate(fixed, rules) == []
