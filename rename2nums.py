#!usr/bin/env python

import glob
import os

oldfiles = sorted(glob.glob("*.*"))
digits = len(str(len(oldfiles)))
names = [str(num).zfill(digits) for num in range(1, len(oldfiles) + 1)]
for i, oldfile in enumerate(oldfiles):
    newfile = "%s.%s" % (names[i], oldfile.split(".")[-1])
    os.rename(oldfile, newfile)
    print("%s -> %s" % (oldfile, newfile))

