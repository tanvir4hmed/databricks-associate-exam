import json,re
from pathlib import Path
from html.parser import HTMLParser
R=Path(__file__).resolve().parents[1]
q=json.loads((R/'dist/data.json').read_text(encoding='utf-8'))
assert [x['id'] for x in q]==list(range(1,281))
class SafeHTML(HTMLParser):
    def handle_starttag(self,tag,attrs):
        assert tag not in ['script','iframe','form','input'],tag
        for k,v in attrs:
            assert not k.startswith('on'),k
            if k=='src': assert (R/'dist'/v).is_file(),v
for x in q:
    assert x['answer'] and len(x['choices'])>=4,x['id']
    assert x['gpt']['body'] and len(x['gpt']['body'].split())<80,x['id']
    assert x['gpt']['source'].startswith('https://')
    p=SafeHTML();p.feed(x['html'])
    for c in x['choices']:p.feed(c['html'])
    for c in x['discussion']:assert c['user'] and c['body']
print(f'PASS: {len(q)} numbered questions, answers, images, sanitized HTML, and concise GPT notes.')
