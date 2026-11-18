from pathlib import Path

from nlp_regulatory_obligation_tracker.desk_cli import load_case


def test_official_filing_and_formal_material_requirements_match():
    fixture = Path(__file__).parents[1] / 'fixtures'
    output = load_case(fixture / 'work.json', fixture / 'business.json')
    assert output[0]['route'] == '原路径'
    assert output[0]['needed'] == ['连续经营证明']
    assert output[0]['other_route'] == ['D-27']
    assert output[1]['route'] == '待核'
