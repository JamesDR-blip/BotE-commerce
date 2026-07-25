import pandas as pd
from validators.fashion import FashionValidator

def test_fashion_autofix_and_validate() -> None:
    frame = pd.DataFrame({"Size": [" s "], "Color": [" red "], "Price": ["100"]})
    fixed = FashionValidator().autofix(frame)
    assert fixed.loc[0, "Size"] == "S"
    assert FashionValidator().validate(fixed, {}) == []
