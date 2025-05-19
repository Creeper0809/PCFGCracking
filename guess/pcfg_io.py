import os,codecs
from collections import OrderedDict

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
    from guess.pcfg_guesser import Type
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
            name = prefix + idx

            grouped = OrderedDict()
            for v, p in items:
                grouped.setdefault(p, []).append(v)

            grammar[name] = [
                {Type.TERMINALS: values, Type.PROB: prob}
                for prob, values in grouped.items()
            ]

    base_structures=[]
    gd=os.path.join(base_directory,'Grammar')
    if os.path.isdir(gd):
        data=load_indexed_prob(gd,'ASCII')
        for items in data.values():
            for value,prob in items:
                replacements=[]
                token=''
                for char in value:
                    if char.isalpha():
                        if token: replacements.append(token)
                        token=char
                    else:
                        token+=char
                i = 0
                while i < len(replacements):
                    if replacements[i].startswith('A') or replacements[i].startswith('H'):
                        length = replacements[i][1:]
                        replacements.insert(i + 1, 'C' + length)
                        i += 1
                    i += 1

                if token: replacements.append(token)
                base_structures.append({Type.PROB:prob, Type.REPLACEMENTS :replacements})
    return grammar,base_structures
