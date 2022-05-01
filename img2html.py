#!usr/bin/env python

import glob

images = ["<img src='%s' style='max-width:100%%' />" % f
          for f in sorted(glob.glob("*.png"))]
html = "<html><body>\n%s\n</body></html>" % '\n'.join(images)
print(html)

"""
bash to rename files
for i in *.jpg; do mv $i $(echo $i | sed 's/[^0-9]//g').jpg; done
for i in `seq 0 9`; do mv "$i.jpg" "0$i.jpg"; done
"""

