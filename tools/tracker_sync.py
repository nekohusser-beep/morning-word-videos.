#!/usr/bin/env python3
"""Rebuild overnight/TRACKER.md (plain-text mirror) from overnight/Claude-Work-Tracker.xlsx.
Move Done rows older than 14 days to the Archive tab by hand, then rerun this script.
Also archives Done rows older than 14 days is NOT automatic; move them by hand to the Archive tab."""
import openpyxl,sys,os
X='overnight/Claude-Work-Tracker.xlsx';M='overnight/TRACKER.md'
wb=openpyxl.load_workbook(X)
rz=[r[1] for r in wb['Standing rules'].iter_rows(min_row=2,values_only=True) if r[0] and str(r[0]).startswith('RULE ZERO')]
out=(['# RULE ZERO (read first, applies to every thread and every model): '+rz[0],''] if rz else [])+['# TRACKER (auto-generated mirror of Claude-Work-Tracker.xlsx; edit the xlsx, never this file)','']
w=wb['Where we are']
out.append('Last updated: %s'%w['B2'].value);out.append('')
t=wb['Tasks'];rows=[[ (str(c) if c is not None else '') for c in r] for r in t.iter_rows(min_row=2,values_only=True) if any(r)]
cnt={}
for r in rows: cnt[r[3]]=cnt.get(r[3],0)+1
out.append('Counts: '+', '.join('%s %d'%(k,v) for k,v in sorted(cnt.items())));out.append('')
for st in ['In progress','Blocked','Not started','On hold','Done']:
    sel=[r for r in rows if r[3]==st]
    if not sel: continue
    out.append('## %s (%d)'%(st,len(sel)))
    for r in sel:
        line='- [%s] %s | %s'%(r[0],r[1],r[2])
        if r[4]: line+=' | NEXT: '+r[4]
        if r[5]: line+=' | WAITING ON: '+r[5]
        line+=' | %s | %s'%(r[6],r[7]);out.append(line)
    out.append('')
for name in ['Standing rules','How it was done']:
    if name in wb.sheetnames:
        out.append('## '+name)
        for r in wb[name].iter_rows(min_row=2,values_only=True):
            if any(r): out.append('- '+' :: '.join(str(c) for c in r if c))
        out.append('')
open(M,'w').write('\n'.join(out))
print('wrote',M,len(rows),'task rows')
