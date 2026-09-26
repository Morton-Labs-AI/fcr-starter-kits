#!/usr/bin/env python3
"""Reproduce the display dataset from pinned MIT files; no OpenMC execution.
Usage: python3 tools/project_beavrs.py [--check]
"""
import ast,csv,hashlib,io,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/beavrs/source'
OUT=ROOT/'public/beavrs'
REV='1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22'
BASE=f'https://github.com/mit-crpg/BEAVRS/blob/{REV}/'
check='--check' in sys.argv
outputs={}
def write(path,value):
 outputs[path]=(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def read(p): return (SOURCE/p).read_text()
def rows(p): return list(csv.reader(io.StringIO(read(p))))
def number(s):
 try:
  f=float(s)
  return f if abs(f)!=float('inf') and f==f else None
 except (ValueError,TypeError): return None
def position(s):
 m=re.fullmatch(r'([A-R])\s*_*\s*0*(\d+)',s.strip()); assert m,s
 return m[1]+str(int(m[2]))
def assignments(path):
 out={}
 for n in ast.walk(ast.parse(read(path))):
  if isinstance(n,ast.Assign):
   for t in n.targets:
    k=t.id if isinstance(t,ast.Name) else t.attr if isinstance(t,ast.Attribute) else None
    try: out[k]=ast.literal_eval(n.value)
    except (ValueError,TypeError): pass
 return out
cp='models/openmc/beavrs/constants.py'; c=assignments(cp)
core=assignments('models/openmc/beavrs/core.py'); ass=assignments('models/openmc/beavrs/assemblies.py')
params={}
for n in ast.parse(read(cp)).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
  k=n.targets[0].id; v=c.get(k)
  if isinstance(v,(float,int)):
   comment=read(cp).splitlines()[n.lineno-1].split('#',1)[-1].strip()
   params[k]={'unit':{'h2oDens':'g/cm³','nominalBoronPPM':'ppm','operating_temperature':'K','n_nozzle_pins':'count','nozzle_water_vol_frac':'volume fraction','nozzle_ss_vol_frac':'volume fraction'}.get(k,'cm'),'value':v,'source':cp,'line':n.lineno,'note':comment,'evidence':'estimated' if re.search('arbitrary|guess|approx|no source|Assumed',comment) else 'source-model'}
# Only explicit geometry constants are converted from the source's centimetres.
geometry={k:round(v/100,9) for k,v in c.items() if isinstance(v,(int,float)) and k in params and k not in ['h2oDens','nominalBoronPPM','operating_temperature','n_nozzle_pins','nozzle_water_vol_frac','nozzle_ss_vol_frac']}
lattice=[[p.strip() for p in row] for row in ass['pin_lattice_template']]
patterns={}
for n in ast.walk(ast.parse(read('models/openmc/beavrs/assemblies.py'))):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and n.args and isinstance(n.args[0],ast.Tuple):
  tup=n.args[0]
  if len(tup.elts)==2 and isinstance(tup.elts[0],ast.Constant) and isinstance(tup.elts[1],ast.Dict):
   patterns[tup.elts[0].value]=[k.value for k,v in zip(tup.elts[1].keys,tup.elts[1].values) if isinstance(v,ast.Name) and v.id=='u_bp']
# Cycle 2's 12-absorber layout differs from cycle 1: read its diagram directly.
special=[]
for a,b in re.findall(r'\\renewcommand\{\\Node([A-Q])([A-Q])\}\{B\}',read('docs/specifications/specifications/assy/figs/12ba_c2.tex')):
 special.append(lattice[ord(a)-65][ord(b)-65])
patterns['12c2']=special
mass={1:{},2:{}}; cycle=1
for row in rows('measurements/assem_mass_loading.csv'):
 if row and row[0].startswith('Cycle'): cycle=int(row[0][-1])
 elif row and number(row[1] if len(row)>1 else '') is not None:
  mass[cycle][position(row[0])]={'uranium_g':float(row[1]),'u235_g':float(row[2]),'initial_enrichment':float(row[3])}
cycles={1:[],2:[]}
for r,row in enumerate(core['core_lattice_template']):
 for col,key in enumerate(row):
  if key not in core['enr_positions']: continue
  p=position(key); ba=core['ba_positions'].get(key,'no BAs')
  cycles[1].append({'id':p,'row':r-2,'col':col-2,'x':round((col-9)*geometry['latticePitch'],9),'z':round((r-9)*geometry['latticePitch'],9),'nominal_enrichment':float(core['enr_positions'][key][:-1]),'previous':None,'fresh':True,'absorber_pattern':ba,'instrument':key in core['instr_positions'],'bank':core['rcca_positions'].get(key),'mass':mass[1][p]})
byid={a['id']:a for a in cycles[1]}
fig='docs/specifications/specifications/core/figs/cat_enr_ba_zones_c2.tex'
for line in read(fig).splitlines():
 m=re.search(r'\\node \[Assembly, fill=\\(noenr|lowenr|highenr).*\{(.*?)\}; % ([A-R]\d+)',line)
 if not m: continue
 kind,content,p=m.groups(); old=re.search(r'\\scriptsize ([A-R]\d+)',content); prev=position(old[1]) if old else None
 ba=re.search(r'\\small (\d+)',content); pattern=ba[1] if ba else 'no BAs'
 if pattern=='12': pattern='12c2'
 a={**byid[p],'previous':prev,'fresh':kind!='noenr','absorber_pattern':pattern,'mass':mass[2].get(p) if not prev else mass[1][prev],'nominal_enrichment':byid[prev]['nominal_enrichment'] if prev else 3.2 if kind=='lowenr' else 3.4}
 cycles[2].append(a)
for cy in cycles:
 cycles[cy].sort(key=lambda a:(a['row'],a['col']))
 assert len(cycles[cy])==193
assert sum(a['fresh'] for a in cycles[2])==64
power={1:[],2:[]}; cycle=1
for row in rows('measurements/power_history/power_history.csv'):
 if row and row[0].startswith('Cycle'): cycle=int(row[0][-1])
 elif len(row)>1 and number(row[0]) is not None and (not row[1].strip() or number(row[1]) is not None): power[cycle].append([number(row[0]),number(row[1])])
boron={1:[],2:[]}
for row in rows('measurements/boron_letdown.csv')[3:]:
 for cy,offset in [(1,1),(2,6)]:
  if len(row)>offset+2 and number(row[offset+1]) is not None: boron[cy].append([number(row[offset+1]),number(row[offset+2]),number(row[offset])])
hzp={1:[],2:[]}; exp='docs/specifications/expdata/expdata.tex'; ex=read(exp)
for cy in (1,2):
 block=ex.split('\\label{tbl:meas_c%dphys}'%cy)[1].split('\\end{tabular}')[0]
 for line in block.splitlines():
  if '&' not in line or 'multicolumn' in line: continue
  cells=line.replace('\\ac{ARO}','All rods out').replace('\\\\','').strip().split('&')
  if len(cells)!=6: continue
  for i,(metric,unit) in enumerate([('Critical boron','ppm'),('Rod-bank worth','pcm'),('Isothermal temperature coefficient','pcm/°F')]):
   value=number(cells[i*2+1].strip())
   if value is not None: hzp[cy].append({'metric':metric,'configuration':cells[i*2].strip(),'value':value,'unit':unit,'uncertainty':None})
# Detector campaigns load independently, preserving source values and uncertainty columns.
campaigns={1:[],2:[]}
for cy in (1,2):
 for folder in sorted((SOURCE/f'measurements/detector_signals/cycle_{cy}').iterdir(),key=lambda p:int(p.name) if p.name.isdigit() else -1):
  if not folder.is_dir() or not folder.name.isdigit(): continue
  rel=folder.relative_to(SOURCE).as_posix(); day=int(folder.name)
  summary=rows(rel+'/summary.csv'); radial={position(row[0]):number(row[1]) for row in rows(rel+'/radial_measurements_full.csv') if len(row)>1 and row[0].strip()}
  ar=rows(rel+'/axial_signals.csv'); axial={}
  for i in range(1,len(ar[0]),2):
   p=position(ar[0][i]); axial[p]=[[number(row[0]),number(row[i]),number(row[i+1]) if i+1<len(row) else None] for row in ar[1:] if len(row)>i and number(row[0]) is not None]
  entry={'day':day,'burnup':number(summary[1][1]),'inlet_f':number(summary[2][1]),'url':f'beavrs/detectors/c{cy}-{day}.json','source':rel,'locations':len(radial)}
  campaigns[cy].append(entry)
  write('detectors/c%d-%d.json'%(cy,day),{'radial':radial,'axial':axial,'summary':summary,'source':rel,'normalization':f'Original full-core, not tilt-corrected. Source normalization targets a sum equal to the number of measured locations. This file sums to {sum(v for v in radial.values() if v is not None):.6f} for {len(radial)} locations. Values are preserved without renormalization.','axial_note':'Source Location in cm, bottom to top; signal and uncertainty columns preserved verbatim. Uncertainty is not reinterpreted as an absolute confidence interval.'})
write('dataset.json',{'schema_version':1,'revision':REV,'source_url':BASE,'units':{'length':'m','source_length':'cm','up_axis':'Y','orientation':'Top view: R through A left to right; rows 1 through 15 top to bottom. Source +y maps to display -z.'},'geometry':geometry,'parameters':params,'pin_lattice':lattice,'absorber_patterns':patterns,'cycles':{str(cy):{'assemblies':cycles[cy],'power':power[cy],'boron':boron[cy],'hzp':hzp[cy],'campaigns':campaigns[cy]} for cy in (1,2)},'measurement_notes':{'power':'Calendar days since beginning of cycle; percent rated power. Source sample spacing retained. The separate 101 cooling-days annotation between cycles is not a power observation.','boron':'Effective full-power days, boron ppm, source MWD column. Not calendar days.','hzp':'Cycle 1 bank worths are measured along an insertion sequence; cycle 2 reports individual banks. No uncertainty provided in these tables.','detectors':'Published processed observations, not simulation. Missing locations remain unmeasured. Campaign day is elapsed calendar day; absolute dates are not supplied.'}})
files=[]
for p in sorted(SOURCE.rglob('*')):
 if p.is_file(): files.append({'path':p.relative_to(SOURCE).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'url':BASE+p.relative_to(SOURCE).as_posix()})
write('manifest.json',{'repository':'https://github.com/mit-crpg/BEAVRS','revision':REV,'license':'MIT','files':files,'derived':[{'path':k,'sha256':hashlib.sha256(v).hexdigest()} for k,v in sorted(outputs.items())],'limitations':['Benchmark reconstruction, not fabrication CAD.','Unspecified primary-loop equipment and routing are illustrative.','Source-model assumptions retain their original notes.','Cycle 2 reused assemblies show initial enrichment, not depleted isotopic compositions.','No neutronics, thermal-hydraulics, structural, or depletion solver executed.']})
for p,b in outputs.items():
 target=OUT/p
 if check:
  assert target.read_bytes()==b, 'Stale: '+str(target)
 else:
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
if not check:
 (OUT/'LICENSE.txt').write_bytes((SOURCE/'LICENSE').read_bytes())
 with zipfile.ZipFile(OUT/'reproduction.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(SOURCE.rglob('*')):
   if p.is_file():
    info=zipfile.ZipInfo('research/beavrs/source/'+p.relative_to(SOURCE).as_posix(),(2025,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
  for path in ['tools/project_beavrs.py','src/beavrs/geometry.ts','src/beavrs/contract.ts','research/beavrs/README.md']:
   if (ROOT/path).exists():
    info=zipfile.ZipInfo(path,(2025,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(ROOT/path).read_bytes())
print('BEAVRS:',len(files),'source files;',sum(len(v) for v in campaigns.values()),'detector campaigns; deterministic check' if check else 'projected')
