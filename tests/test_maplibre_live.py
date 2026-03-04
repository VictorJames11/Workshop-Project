from simulated_city.maplibre_live import (
    _inject_renderer_binding,
    car_popup_text,
    resolve_node_lnglat,
    resolve_segment_lnglat,
)


def test_inject_renderer_binding_minified_export() -> None:
    content = "var vjn={render:EPr};export{oDt as MapLibreRenderer,vjn as default};"
    out = _inject_renderer_binding(content)
    assert "const MapLibreRenderer=oDt;" in out
    assert "export{oDt as MapLibreRenderer" in out


def test_inject_renderer_binding_keeps_existing_binding() -> None:
    content = "const MapLibreRenderer=oDt;export{oDt as MapLibreRenderer};"
    out = _inject_renderer_binding(content)
    assert out == content


def test_inject_renderer_binding_parses_alt_export() -> None:
    content = "export{A$1 as MapLibreRenderer,foo as default};"
    out = _inject_renderer_binding(content)
    assert "const MapLibreRenderer=A$1;" in out
    assert "export{A$1 as MapLibreRenderer" in out


def test_resolve_node_lnglat_from_defaults() -> None:
    lng, lat = resolve_node_lnglat("N2")
    assert isinstance(lng, float)
    assert isinstance(lat, float)


def test_resolve_segment_lnglat_midpoint() -> None:
    midpoint = resolve_segment_lnglat(
        44105317,
        segment_node_pairs={44105317: ("N2", "N3")},
    )
    assert len(midpoint) == 2
    assert midpoint[0] > 12.56


def test_car_popup_text_contains_core_fields() -> None:
    text = car_popup_text(
        {
            "car_id": "car-01",
            "status": "arrived",
            "origin": "N1",
            "destination": "N6",
            "tick": 3,
        }
    )
    assert "car=car-01" in text
    assert "od=N1->N6" in text
