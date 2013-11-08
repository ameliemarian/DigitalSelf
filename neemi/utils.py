

def cleanDict(dicto, string):
    if type(dicto) is dict:
        for key,value in dicto.iteritems():
            print [key]
            if string in key:
                newkey = key.replace(string,'')
                dicto[newkey] = dicto[key]
                del dicto[key]
    
            if type(value) is dict:
                value = cleanDict(dicto=value,string=string)
            elif type(value) is list:
                for item in value:
                    item = cleanDict(dicto=item,string=string)
            elif type(value) is unicode:
                # print [value]
                if string in value:
                    #print[value]
                    newvalue = value.replace(string,'')
                    dicto[key] = newvalue
                    #return value
    elif type(dicto) is list:
        for item in dict:
            item = cleanDict(dicto=item,string=string)
    elif type(dicto) is unicode:
        if string in dicto:
            #print[dicto]
            newdicto = dicto.replace(string,'')
            dicto = newdicto
    return dicto

def cleanDictField(dicto):
    if type(dicto) is dict:
        for key,value in dicto.iteritems():
            if '.' in key:
                newkey = key.replace('.','\DOT')
                dicto[newkey] = dicto[key]
                del dicto[key]
            if '$' in key:
                newkey = key.replace('$','\DOL')
                dicto[newkey] = dicto[key]
                del dicto[key]
            if type(value) is dict:
                value = cleanDictField(dicto=value)
            elif type(value) is list:
                for item in value:
                    item = cleanDictField(dicto=item)
    elif type(dicto) is list:
        for item in dict:
            item = cleanDictField(dicto=item)
    return dicto

