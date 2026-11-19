import json
from pathlib import Path

from nlp_regulatory_obligation_tracker.desk_cli import load_review
from nlp_regulatory_obligation_tracker.review import review

FIXTURES = Path(__file__).parents[1] / 'fixtures'


def load():
    return load_review(FIXTURES / 'review-case.json', FIXTURES / 'review-registry.json')


def matters(result):
    return {matter['matter']: matter for matter in result['matters']}


def test_classification_distinguishes_three_outcomes():
    result = load()
    assert result['summary'] == {'应办理': ['A-3'], '不适用': ['A-1', 'A-2'], '不能确定': ['A-4']}
    found = matters(result)
    assert found['A-1']['route'] == '原路径'
    assert found['A-1']['basis']['receipt'] == 'AC-17'
    assert found['A-3']['route'] == '现路径'
    assert found['A-4']['route'] == '待核'
    assert found['A-4']['todos'] == ['补交业务受理处签发的受理回执，确认是否已按旧办法受理']


def test_late_evidence_only_changes_the_matter_it_proves():
    result = load()
    found = matters(result)
    assert [item['ref'] for item in found['A-1']['evidence']] == ['AC-17']
    assert found['A-2']['basis']['receipt'] == 'AC-23'
    assert found['A-2']['classification'] == '不适用'
    submission = next(item for item in found['A-2']['evidence'] if item['ref'] == 'AC-19')
    assert submission['reliable'] is False


def test_removing_late_evidence_leaves_other_matters_unchanged():
    case = json.loads((FIXTURES / 'review-case.json').read_text(encoding='utf-8'))
    registry = json.loads((FIXTURES / 'review-registry.json').read_text(encoding='utf-8'))
    registry['filings'] = [filing for filing in registry['filings'] if filing['ref'] != 'AC-23']
    found = matters(review(case, registry))
    assert found['A-2']['classification'] == '不能确定'
    assert found['A-1']['classification'] == '不适用'
    assert found['A-3']['classification'] == '应办理'


def test_material_reuse_requires_matching_issuer_and_period():
    found = matters(load())
    obligations = {entry['clause']: entry for entry in found['A-3']['obligations']}
    assert obligations['final-12#3']['satisfied_by'] == ['M-1']
    assert obligations['final-12#3']['rejected'] == [{'id': 'M-2', 'reason': '签发主体不符（行业协会≠登记机关）'}]
    assert obligations['final-12#2']['rejected'] == [{'id': 'M-3', 'reason': '认定期间不符（2024年度≠2025年度）'}]
    assert found['A-3']['todos'] == ['补交连续经营证明（登记机关签发，覆盖2025年度）']


def test_disposal_explains_delivered_materials_and_drafts():
    found = matters(load())
    delivered = {item['id']: item for item in found['A-3']['disposal']['delivered']}
    assert delivered['M-1']['handling'] == '留用'
    assert 'final-12#3' in delivered['M-1']['detail']
    assert delivered['M-2']['handling'] == '留存不计入'
    assert '签发主体不符' in delivered['M-2']['detail']
    assert delivered['M-3']['handling'] == '留存不计入'
    assert '认定期间不符' in delivered['M-3']['detail']
    drafts = {item['id']: item for item in found['A-3']['disposal']['drafts']}
    assert drafts['M-4']['handling'] == '可修改或作废'
    assert 'final-12#2' in drafts['M-4']['detail']


def test_draft_and_supplement_create_no_obligations():
    result = load()
    sources = {entry['clause'] for matter in result['matters'] for entry in matter['obligations']}
    assert sources == {'final-12#2', 'final-12#3'}
    stages = {clause['source']: clause['operative'] for clause in result['clauses']}
    assert stages['draft-12'] is False
    assert stages['supp-12'] is False
    assert stages['final-12'] is True
