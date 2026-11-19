"""受理回执与通告条款核对。

结合可靠受理回执，把每项业务区分为应办理、不适用和现有材料不能确定。
回执按事项归集，后补证据只改变它能证明的事项；已交材料不可改，只能核对
能否在确认后的路径里留用；草稿可修改或作废，不产生办理义务。
"""
from datetime import date

from .notice import parse_documents

ACCEPTANCE_KIND = '受理回执'
DELIVERED_STAGE = '已交'
DRAFT_STAGE = '草稿'
PENDING_STAGE = '待交'
CLASSIFICATIONS = ('应办理', '不适用', '不能确定')


def _reliable(filing, publisher):
    return (
        filing.get('kind') == ACCEPTANCE_KIND
        and filing.get('issuer') == publisher
        and bool(filing.get('received'))
    )


def _classify(evidence, cutoff):
    reliable = [item for item in evidence if item['reliable']]
    if reliable:
        chosen = min(reliable, key=lambda item: item['received'])
        if date.fromisoformat(chosen['received']) < cutoff:
            return '原路径', '不适用', chosen['ref'], (
                f"受理回执{chosen['ref']}载明{chosen['received']}受理，"
                f"早于界限{cutoff.isoformat()}，属已按旧办法受理"
            )
        return '现路径', '应办理', chosen['ref'], (
            f"受理回执{chosen['ref']}载明{chosen['received']}受理，"
            f"不早于界限{cutoff.isoformat()}，按现行办法办理"
        )
    if evidence:
        return '待核', '不能确定', None, '仅有提交回执或回执并非受理处签发，现有材料不能确定是否已受理'
    return '待核', '不能确定', None, '没有受理回执，现有材料不能确定是否已受理'


def _match_requirement(materials, requirement):
    matched, rejected = [], []
    for material in materials:
        if material.get('stage') != DELIVERED_STAGE or material.get('title') != requirement['material']:
            continue
        reasons = []
        if material.get('issuer') != requirement['issuer']:
            reasons.append(f"签发主体不符（{material.get('issuer')}≠{requirement['issuer']}）")
        if material.get('period') != requirement['period']:
            reasons.append(f"认定期间不符（{material.get('period')}≠{requirement['period']}）")
        if reasons:
            rejected.append({'id': material['id'], 'reason': '；'.join(reasons)})
        else:
            matched.append(material['id'])
    return matched, rejected


def _evaluate_obligations(operative, requirements, materials, classification):
    obligations = []
    for clause in operative:
        requirement = requirements.get(clause['id'])
        if requirement is None:
            continue
        entry = {
            'clause': clause['id'],
            'condition': clause['condition'],
            'action': clause['action'],
            'exceptions': clause['exceptions'],
            'status': classification,
            'requires': {
                'material': requirement['material'],
                'issuer': requirement['issuer'],
                'period': requirement['period'],
            },
        }
        if classification == '应办理':
            matched, rejected = _match_requirement(materials, requirement)
            entry['satisfied_by'] = matched
            entry['rejected'] = rejected
        elif classification == '不适用':
            entry['note'] = '例外成立，无需补交'
        else:
            entry['note'] = '待受理状态确认后核对材料'
        obligations.append(entry)
    return obligations


def _basis_clauses(operative, classification, obligations):
    if classification == '不适用':
        ids = [clause['id'] for clause in operative if '原路径' in clause['action']]
        ids += [clause['id'] for clause in operative if any('受理' in item for item in clause['exceptions'])]
        return sorted(set(ids))
    if classification == '应办理':
        return [entry['clause'] for entry in obligations]
    return []


def _todos(classification, obligations, materials, publisher):
    if classification == '不能确定':
        return [f'补交{publisher}签发的受理回执，确认是否已按旧办法受理']
    if classification == '不适用':
        return []
    todos = [
        f"补交{entry['requires']['material']}（{entry['requires']['issuer']}签发，覆盖{entry['requires']['period']}）"
        for entry in obligations
        if not entry['satisfied_by']
    ]
    todos.extend(f"提交{material['title']}" for material in materials if material.get('stage') == PENDING_STAGE)
    return todos


def _disposal(materials, obligations, classification):
    satisfied = {mid for entry in obligations for mid in entry.get('satisfied_by', [])}
    rejected = {item['id']: (entry['clause'], item['reason']) for entry in obligations for item in entry.get('rejected', [])}
    clause_by_title = {entry['requires']['material']: entry['clause'] for entry in obligations}
    delivered, drafts = [], []
    for material in materials:
        stage = material.get('stage')
        if stage == DELIVERED_STAGE:
            if material['id'] in satisfied:
                clause = next(entry['clause'] for entry in obligations if material['id'] in entry.get('satisfied_by', []))
                delivered.append({'id': material['id'], 'handling': '留用', 'detail': f'满足条款{clause}，计入已确认路径'})
            elif material['id'] in rejected:
                clause, reason = rejected[material['id']]
                delivered.append({'id': material['id'], 'handling': '留存不计入', 'detail': f'{reason}，不能用于满足{clause}'})
            elif classification == '不能确定':
                delivered.append({'id': material['id'], 'handling': '待路径确认', 'detail': '受理状态未确认，暂不计入'})
            elif classification == '不适用':
                delivered.append({'id': material['id'], 'handling': '留存不计入', 'detail': '补资料义务不适用，无需补交'})
            else:
                delivered.append({'id': material['id'], 'handling': '留存不计入', 'detail': '与本次义务条款不对应'})
        elif stage == DRAFT_STAGE:
            detail = '草稿不产生办理义务，可修改或作废'
            clause = clause_by_title.get(material.get('title'))
            if clause is not None:
                detail += f'；如用于履行{clause}，须按确认后的路径正式提交'
            drafts.append({'id': material['id'], 'handling': '可修改或作废', 'detail': detail})
    return {'delivered': delivered, 'drafts': drafts}


def review(case, registry):
    publisher = registry['publisher']
    cutoff = date.fromisoformat(case['cutoff'])
    clauses = parse_documents(registry.get('documents', []))
    operative = [clause for clause in clauses if clause['operative'] and clause['kind'] == '义务']
    requirements = {item['clause']: item for item in case.get('requirements', [])}
    filings = registry.get('filings', [])
    matters = []
    for application in case['applications']:
        bound = [filing for filing in filings if filing.get('matter') == application['id']]
        evidence = [
            {
                'ref': filing['ref'],
                'kind': filing.get('kind'),
                'issuer': filing.get('issuer'),
                'received': filing.get('received'),
                'reliable': _reliable(filing, publisher),
            }
            for filing in bound
        ]
        route, classification, receipt, reason = _classify(evidence, cutoff)
        materials = application.get('materials', [])
        obligations = _evaluate_obligations(operative, requirements, materials, classification)
        matters.append({
            'matter': application['id'],
            'institution': application.get('institution'),
            'route': route,
            'classification': classification,
            'basis': {
                'receipt': receipt,
                'reason': reason,
                'clauses': _basis_clauses(operative, classification, obligations),
            },
            'evidence': evidence,
            'obligations': obligations,
            'todos': _todos(classification, obligations, materials, publisher),
            'disposal': _disposal(materials, obligations, classification),
        })
    summary = {key: [m['matter'] for m in matters if m['classification'] == key] for key in CLASSIFICATIONS}
    return {'clauses': clauses, 'matters': matters, 'summary': summary}
