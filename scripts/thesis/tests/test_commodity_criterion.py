import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import commodity_criterion as cc  # noqa: E402


def test_classify_thresholds():
    assert cc.classify(60.0) == "strong"
    assert cc.classify(59.99) == "moderate"
    assert cc.classify(40.0) == "moderate"
    assert cc.classify(39.9) == "not"
    assert cc.classify(float("nan")) == "missing"


def test_panels_have_30_unique_countries_and_names():
    codes = [c for v in cc.PANELS.values() for c in v]
    assert len(codes) == 30 and len(set(codes)) == 30
    assert set(codes) == set(cc.NAMES)


def test_source_table_matches_report_headlines():
    p = pd.read_csv(cc.PROFILES, keep_default_na=False, na_values=[""])
    assert (p.share_2021_2023 > 60).sum() == 103     # UNCTAD SCD 2025 headline
    assert (p.share_2012_2014 > 60).sum() == 106


def test_classification_is_deterministic_and_complete():
    a, b = cc.classification(), cc.classification()
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 60 and not (a["class"] == "missing").any()
    w = cc.wide(a)
    c = cc.counts(w).set_index("panel")
    assert c.loc["all30", "n"] == 30
    assert c.loc["all30", "ge60"] == 27 and c.loc["all30", "ge40"] == 29
    assert set(w[w.class_2021_2023 != "strong"].country) == {"MX", "ID", "GE"}


def test_missing_country_not_imputed():
    p = pd.read_csv(cc.PROFILES, keep_default_na=False, na_values=[""])
    p = p[p.country_name_pdf != "Kazakhstan"]
    cl = cc.classification(p)
    assert (cl[cl.country == "KZ"]["class"] == "missing").all()
    assert cl[cl.country == "KZ"].share.isna().all()


def test_ce_by_class_counts_and_values():
    ce = pd.DataFrame({"method": "aci", "h": 3, "unit": ["KZ", "MX"], "n": 50, "coverage": [0.88, 0.95],
                       "panel_sample": "design13_exploratory"})
    ce["ce"] = (ce.coverage - 0.9).abs()
    w = cc.wide(cc.classification())
    t = cc.ce_by_class(ce, w, 60).set_index(["cut", "group"])
    assert t.loc[("design13_exploratory", "qualify"), "n_countries"] == 1
    assert abs(t.loc[("design13_exploratory", "qualify"), "mean_ce"] - 0.02) < 1e-12
    assert abs(t.loc[("design13_exploratory", "not_qualify"), "mean_ce"] - 0.05) < 1e-12
    assert abs(t.loc[("pooled30", "not_qualify"), "mean_ce"] - 0.05) < 1e-12


def test_namibia_not_read_as_nan():
    ce = cc.per_country_ce()
    assert "NA" in set(ce.unit)
