import math

def digs(mn, mx):
    predigs = int(math.floor(math.log10(abs(mn-mx))))
    postdigs = 7 - predigs
    step = 10**(2-postdigs)
    scrange = 10.0**predigs
    lower = (math.floor(mn / scrange) - 1.0) * scrange
    upper = (math.ceil(mx / scrange) + 1.0) * scrange
    print "Predigs=", predigs, "Postdigs=", postdigs, "step=", step, "max=",scrange,"lower=",lower,"upper=",upper


    
