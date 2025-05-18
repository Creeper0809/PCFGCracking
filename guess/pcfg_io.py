import os,codecs

def load_indexed_prob(folder,encoding):
    data={}
    for fn in os.listdir(folder):
        if not fn.endswith('.txt'): continue
        key=fn[:-4]
        path=os.path.join(folder,fn)
        lst=[]
        with codecs.open(path,'r',encoding=encoding) as f:
            for line in f:
                v,p=line.rstrip('\n').split('\t')
                lst.append((v,float(p)))
        data[key]=lst
    return data

def load_pcfg_data(base_directory,encoding):
    grammar={}
    mapping=[
        ('Keyboard','K'),
        ('Years','Y'),
        ('Alpha','A'),
        ('Capitalization','C'),
        ('Digits','D'),
        ('Special','S'),
        ('Korean','H')]
    for folder,prefix in mapping:
        d=os.path.join(base_directory,folder)
        if not os.path.isdir(d): continue
        data=load_indexed_prob(d,encoding)
        for idx,items in data.items():
            name=prefix+idx
            grammar[name]=[{'terminals':[v],'prob':p} for v,p in items]
    base_structures=[]
    gd=os.path.join(base_directory,'Grammar')
    if os.path.isdir(gd):
        data=load_indexed_prob(gd,'ASCII')
        for items in data.values():
            for val,prob in items:
                reps=[]
                tok=''
                for ch in val:
                    if ch.isalpha():
                        if tok: reps.append(tok)
                        tok=ch
                    else:
                        tok+=ch
                if tok: reps.append(tok)
                base_structures.append({'prob':prob,'replacements':reps})
    prince_structures=[]
    pd=os.path.join(base_directory,'Prince')
    if os.path.isdir(pd):
        data=load_indexed_prob(pd,'ASCII')
        for items in data.values():
            for val,prob in items:
                prince_structures.append({'values':[val],'prob':prob})
    return grammar,base_structures
