from nlp_regulatory_obligation_tracker.notice import parse_documents, parse_sentence


def test_parse_condition_action_and_exception():
    clause = parse_sentence('尚无资质的先补资质证明，按旧办法已受理的除外')
    assert clause['kind'] == '义务'
    assert clause['condition'] == '尚无资质'
    assert clause['action'] == '先补资质证明'
    assert clause['exceptions'] == ['按旧办法已受理']


def test_parse_comma_condition():
    clause = parse_sentence('尚未取得资质的，应当先补资料')
    assert clause['condition'] == '尚未取得资质'
    assert clause['action'] == '应当先补资料'


def test_parse_subject_suffix_condition():
    clause = parse_sentence('取得资质的机构适用第六条')
    assert clause['condition'] == '取得资质'
    assert clause['action'] == '适用第六条'


def test_only_formal_documents_are_operative():
    documents = [
        {'id': 'd1', 'stage': '草案', 'text': '尚未取得资质的，应当先补资料。'},
        {'id': 'f1', 'stage': '正式', 'text': '已经按旧办法受理的，继续走原路径。'},
        {'id': 's1', 'stage': '补充说明', 'text': '取得资质的机构适用第六条。'},
    ]
    clauses = {clause['id']: clause for clause in parse_documents(documents)}
    assert clauses['d1#1']['operative'] is False
    assert clauses['f1#1']['operative'] is True
    assert clauses['s1#1']['operative'] is False
    assert clauses['f1#1']['condition'] == '已经按旧办法受理'
    assert clauses['f1#1']['action'] == '继续走原路径'
