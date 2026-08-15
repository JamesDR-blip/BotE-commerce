from agents.intent_classifier import IntentClassifier


def test_classifier_detects_quality_validation():

    classifier = IntentClassifier(
        {
            "assess_data_quality": (
                "quality",
                "validate",
                "kiểm tra chất lượng",
            )
        }
    )

    assert classifier.classify(
        "Hãy kiểm tra chất lượng dữ liệu sản phẩm"
    ) == (
        "assess_data_quality",
    )


def test_classifier_detects_extraction():

    classifier = IntentClassifier(
        {
            "extract_product_attributes": (
                "extract",
                "brand",
                "model",
                "thuộc tính",
            )
        }
    )

    assert classifier.classify(
        "Lấy brand và model sản phẩm"
    ) == (
        "extract_product_attributes",
    )