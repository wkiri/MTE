# Plot tallies from manually annotated MPF properties, by Matt and Raymond
# mlia-web-external:
# /var/www/brat/data/mpf/matt
# /var/www/brat/data/mpf/raymond
#
# Kiri Wagstaff
# 10/7/20
import pylab as pl
import matplotlib.ticker as ticker
import numpy as np


mpf_docs = ['1998_1378', '1998_1462', '1998_1534', '1998_1803', '1998_1829',
            '1999_1313', '1999_1907', '1999_2063', '2001_1099', '2002_1896']

# for i in *ann; do echo -ne "$i\t" ; grep HasProperty $i | wc -l ; done
matt_cnt = [ 43, 12, 0, 0, 23, 35, 8, 16, 7, 1 ]
raymond_cnt = [ 44, 11, 1, 0, 35, 30, 7, 14, 6, 0 ]
# Determined manually; not sure how to do it automatically
overlap = [ 25, 5, 0, 0, 10, 26, 5, 14, 0, 0 ]


pl.figure()
width = 0.5
bar_width = width - 0.05
shift = 0.23

xvals = np.arange(len(mpf_docs))
pl.bar(xvals - shift, matt_cnt, width=bar_width, label='Matt')
pl.bar(xvals + shift, raymond_cnt, width=bar_width, label='Raymond')
pl.bar(xvals, overlap, width=bar_width * 2, label='Overlap', 
       color='yellow', alpha=0.5)
pl.ylabel('Number of properties', fontsize=14)
pl.gca().set_xticks(xvals)
pl.gca().set_xticklabels(mpf_docs, rotation=30)
pl.yticks(fontsize=14)
pl.xticks(fontsize=14)
pl.legend(fontsize=14)

fig_file = 'mpf-property-counts.png'
pl.savefig(fig_file, bbox_inches='tight')
print('Saved property counts to %s' % fig_file)
