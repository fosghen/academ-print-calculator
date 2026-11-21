from fastapi.testclient import TestClient

from printcalc.app import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_calculator_page_has_main_product_types() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Визитки" in response.text
    assert "Листовки" in response.text
    assert "Брошюры" in response.text
    assert "Баннеры" in response.text


def test_calculate_endpoint_renders_quote() -> None:
    response = client.post(
        "/calculate",
        data={
            "product_type": "business_cards",
            "quantity": "96",
            "material": "smooth",
            "sides": "2",
            "markup_percent": "0",
        },
    )

    assert response.status_code == 200
    assert "360,00" in response.text
    assert "3,75" in response.text


def test_calculate_endpoint_shows_validation_error() -> None:
    response = client.post(
        "/calculate",
        data={
            "product_type": "business_cards",
            "quantity": "100",
            "material": "smooth",
            "sides": "1",
            "markup_percent": "0",
        },
    )

    assert response.status_code == 422
    assert "тираж" in response.text.lower()
