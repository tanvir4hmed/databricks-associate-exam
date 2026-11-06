"""Import the supplied local archive; never fetch ExamTopics or execute saved scripts."""
import argparse, hashlib, json, re, shutil, zipfile
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('raw', type=Path)
args = parser.parse_args()
raw = args.raw.resolve()
dist = ROOT / 'dist'
(dist/'assets').mkdir(parents=True, exist_ok=True)

# Word paragraphs preserve their run text, tabs, line breaks, and hyperlinks.
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(next(raw.glob('*.docx'))) as z:
    doc = ET.fromstring(z.read('word/document.xml'))
def paragraph(p):
    return ''.join(n.text or '' if n.tag.endswith('}t') else '\n' if n.tag.endswith('}br') else '\t' if n.tag.endswith('}tab') else '' for n in p.iter())
text = '\n'.join(paragraph(p) for p in doc.findall('.//w:p', ns))
sections = re.split(r'Question\s+#(\d+)(?:\s*\(Topic:[^)\n]*(?:\)|(?=\n)))?', text)
discussion = {}; audit = []
for i in range(1,len(sections),2):
    number = int(sections[i]); content=sections[i+1]
    comments=[]
    # Each archived comment terminates in an upvote count, including replies.
    chunks=re.split(r'upvoted\s+(\d+)\s+times?',content)
    for pos in range(0,len(chunks),2):
        block=chunks[pos]
        lines=block.strip().splitlines()
        if not lines: continue
        if 'Bottom of Form' in lines:
            lines=lines[lines.index('Bottom of Form')+1:]
        lines=[l for l in lines if l.strip()]
        date=next((j for j,l in enumerate(lines) if re.search(r'\d+\s+(?:years?|months?|days?|hours?|weeks?)',l) and 'ago' in l),None)
        if date is None or date==0: continue
        user=lines[date-1].strip(); age=lines[date]
        bodylines=lines[date+1:]; selected=''
        if bodylines and bodylines[0].startswith('Selected Answer:'):
            selected=bodylines.pop(0).split(':',1)[1].strip()
        body='\n'.join(bodylines).strip()
        # Remove answer-only assertions, retaining short explanations and links.
        norm=re.sub(r'[^a-z0-9 ]',' ',body.lower())
        norm=re.sub(r'\b(correct|answer|ans|option|the|is|it|its|and|right|response|for|sure|respuesta|correcta|es)\b',' ',norm)
        norm=re.sub(r'\b[a-e]+\b',' ',norm).strip()
        keep=bool(norm) and len(norm.split())>=2 or 'http' in body
        audit.append({'question':number,'user':user,'body':body,'kept':bool(keep)})
        if keep: comments.append({'user':user,'age':age,'selected':selected,'body':body,'upvotes':int(chunks[pos+1]) if pos+1<len(chunks) else 0})
    # Upvotes are presentation metadata; restore by block order (including removed comments).
    discussion[number]=comments

images={}
def clean(node, source):
    node=BeautifulSoup(str(node),'html.parser')
    for n in node.select('script,style,.multi-choice-letter,.most-voted-answer-badge'): n.decompose()
    for n in node.find_all(True):
        if n.name=='li': n.name='div'
        if n.name=='img':
            old=n.get('src',''); file=(source.parent/unquote(old)).resolve()
            if not file.is_relative_to(raw) or not file.is_file(): raise ValueError(f'Missing image: {file}')
            name=hashlib.sha256(file.read_bytes()).hexdigest()[:20]+file.suffix.lower()
            shutil.copyfile(file,dist/'assets'/name); images[name]=True
            n.attrs={'src':'assets/'+name,'alt':'Question or answer diagram','loading':'lazy'}
        elif n.name=='a':
            href=n.get('href',''); n.attrs={'href':href,'target':'_blank','rel':'noopener noreferrer'} if href.startswith('https://') else {}
        else: n.attrs={}
    return str(node)

questions=[]
for file in sorted(raw.glob('*.html')):
    soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser')
    for q in soup.select('.exam-question-card'):
        number=int(re.search(r'Question #(\d+)',q.get_text()).group(1))
        choices=[]
        for item in q.select('.multi-choice-item'):
            letter=item.select_one('.multi-choice-letter').get('data-choice-letter')
            choices.append({'letter':letter,'html':clean(item,file),'text':item.get_text(' ',strip=True)})
        answer=q.select_one('.question-answer strong.ml-1')
        chart=q.select_one('[data-chart]')
        questions.append({'id':number,'html':clean(q.select_one('p.card-text'),file),'text':q.select_one('p.card-text').get_text(' ',strip=True),'choices':choices,'answer':answer.get_text(strip=True) if answer else '', 'votes':json.loads(chart['data-chart']) if chart else [],'discussion':discussion.get(number,[]),'hasArchivedDiscussion':number in discussion})
questions.sort(key=lambda q:q['id'])
def answer_words(t):
    return re.sub(r'\s+',' ',re.sub(r'\b(?:correct|answer|ans|option|the|is|it|its|right|response|for|sure|most|voted|[a-e])\b',' ',re.sub(r'[^a-z0-9 ]',' ',t.lower()))).strip()
for q in questions:
    options={answer_words(BeautifulSoup(c['html'],'html.parser').get_text(' ',strip=True)) for c in q['choices']}
    kept=[]
    for c in q['discussion']:
        if answer_words(c['body']) in options:
            for a in audit:
                if a['question']==q['id'] and a['user']==c['user'] and a['body']==c['body']:a['kept']=False
        else:kept.append(c)
    q['discussion']=kept
assert [q['id'] for q in questions]==list(range(1,281))
(ROOT/'content').mkdir(exist_ok=True)
(ROOT/'content/questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'content/import-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'questions':len(questions),'images':len(images),'comments_kept':sum(len(q['discussion']) for q in questions),'comments_removed':sum(not c['kept'] for c in audit),'missing_discussions':[q['id'] for q in questions if not q['hasArchivedDiscussion']]}))
