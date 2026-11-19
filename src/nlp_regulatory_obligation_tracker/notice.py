"""中文通告条款解析。

从通告文本中识别条件、例外和指向的义务。只有正式通告的条款产生办理义务，
草案和机构收到的补充说明仅供对照。
"""
import re

SENTENCE_SPLIT = re.compile(r'[。；;\n]+')
ACTION_MARKERS = ('应当', '应', '须', '先', '继续', '仍按', '适用', '一律')
SUBJECT_SUFFIXES = ('机构', '案件', '单位', '企业')
OPERATIVE_STAGE = '正式'


def split_sentences(text):
    return [part.strip() for part in SENTENCE_SPLIT.split(text) if part and part.strip()]


def _strip_condition(text):
    text = text.strip()
    for suffix in SUBJECT_SUFFIXES:
        if text.endswith(suffix):
            text = text[:-len(suffix)]
            break
    if text.endswith('的'):
        text = text[:-1]
    return text.strip()


def _split_exception(sentence):
    if '除外' not in sentence:
        return sentence, []
    head, _, _ = sentence.partition('除外')
    if '，' in head:
        body, exception = head.rsplit('，', 1)
    else:
        body, exception = '', head
    return body.strip(), [_strip_condition(exception)]


def _split_condition_action(body):
    for sep in ('，', ','):
        if sep in body:
            head, rest = body.split(sep, 1)
            return _strip_condition(head), rest.strip()
    best = None
    for marker in ACTION_MARKERS:
        index = body.find(marker)
        if index > 0:
            head = body[:index]
            if head.endswith('的') or head.endswith(SUBJECT_SUFFIXES):
                if best is None or index < best[0] or (index == best[0] and len(marker) > len(best[1])):
                    best = (index, marker)
    if best is not None:
        index, _ = best
        return _strip_condition(body[:index]), body[index:].strip()
    return None, body.strip()


def parse_sentence(sentence):
    body, exceptions = _split_exception(sentence)
    condition, action = _split_condition_action(body)
    kind = '义务' if any(marker in action for marker in ACTION_MARKERS) else '说明'
    return {'kind': kind, 'condition': condition, 'action': action, 'exceptions': exceptions, 'text': sentence}


def parse_documents(documents):
    clauses = []
    for document in documents:
        stage = document.get('stage')
        for index, sentence in enumerate(split_sentences(document.get('text', '')), 1):
            clauses.append({
                'id': f"{document['id']}#{index}",
                'source': document['id'],
                'stage': stage,
                'operative': stage == OPERATIVE_STAGE,
                **parse_sentence(sentence),
            })
    return clauses
