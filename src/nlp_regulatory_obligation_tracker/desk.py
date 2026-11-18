from datetime import date


class DirectiveRegister:
    def __init__(self, documents, clauses):
        self.official = {document['id'] for document in documents if document['stage'] == '正式'}
        self.clauses = clauses

    def operative(self, route):
        return [clause for clause in self.clauses if clause['source'] in self.official and clause['route'] == route]


class IntakeEligibility:
    def __init__(self, issuer, filings):
        self.issuer = issuer
        self.filings = {item['ref']: item for item in filings}

    def route(self, filing_ref, cutoff):
        if filing_ref is None:
            return '待核', None
        filing = self.filings[filing_ref]
        if filing['issuer'] != self.issuer or not filing.get('received'):
            return '待核', None
        previous = date.fromisoformat(filing['received']) < date.fromisoformat(cutoff)
        return ('原路径' if previous else '现路径'), filing['ref']


class MaterialsDesk:
    def __init__(self, directives):
        self.directives = directives

    def evaluate(self, route, submissions):
        current = {rule['material'] for rule in self.directives.operative(route)}
        have = {item['material'] for item in submissions if item['stage'] == '已交' and item['route'] == route}
        review = [item['id'] for item in submissions if item['route'] != route and route != '待核']
        return {'needed': sorted(current - have), 'other_route': sorted(review)}


def assess(case, registry):
    eligibility = IntakeEligibility(registry['publisher'], registry['filings'])
    directives = DirectiveRegister(registry['documents'], case['clauses'])
    desk = MaterialsDesk(directives)
    results = []
    for application in case['applications']:
        route, filing = eligibility.route(application['filing'], case['cutoff'])
        results.append({'case': application['id'], 'route': route, 'filing': filing,
                        **desk.evaluate(route, application['materials'])})
    return results
