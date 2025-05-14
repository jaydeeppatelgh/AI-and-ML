import spacy

class RequirementAnalyzer:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')

    def analyze(self, text):
        doc = self.nlp(text)
        extracted_info = {
            'name': None,
            'address': None,
            'needs': []
        }

        for ent in doc.ents:
            if ent.label_ == 'ORG':
                extracted_info['name'] = ent.text
            elif ent.label_ == 'GPE':
                extracted_info['address'] = ent.text
            elif 'pharmaceutical' in ent.text.lower():
                extracted_info['needs'].append('pharma supplies')

        return extracted_info
