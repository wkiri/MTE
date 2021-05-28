# Plot the number of relevant documents per year
# Kiri Wagstaff
# 9/13/20
import pylab as pl
import matplotlib.ticker as ticker
import numpy as np


pl.figure()
mpf_yrs = range(1998, 2021)
# Obtained from
# cd /proj/mte/data/corpus-lpsc/mpf/
# ls *txt | cut -f1 -d'_' | sort | uniq -c
mpf_cnt = [68,49,42,46,46,33,56,47,32,22,19,22,13,12,14,18,7,10,6,5,3,16,5]
pl.bar(mpf_yrs, mpf_cnt)
pl.xlabel('Year')
pl.ylabel('Pathfinder-related abstracts')
mpf_file = 'mpf-by-year.png'
pl.savefig(mpf_file, bbox_inches='tight')
print('Saved MPF histogram to %s' % mpf_file)

pl.clf()
phx_yrs = range(2009, 2021)
# Obtained from
# cd /proj/mte/data/corpus-lpsc/phx/
# ls *txt | cut -f1 -d'_' | sort | uniq -c
phx_cnt = cnt=[78,54,44,37,58,36,39,29,29,31,35,20]
pl.bar(phx_yrs, phx_cnt)
pl.xlabel('Year')
pl.ylabel('Phoenix-related abstracts')
phx_file = 'phx-by-year.png'
pl.savefig(phx_file, bbox_inches='tight')
print('Saved PHX histogram to %s' % phx_file)

# Joint plot
pl.clf()
width = 0.5
bar_width = width - 0.05
shift = 0.23
#shift = 0.4
x = np.arange(len(mpf_yrs))
pl.bar(x - shift, mpf_cnt, width=bar_width, label='Pathfinder')
pl.bar(x[phx_yrs[0] - mpf_yrs[0]:] + shift, phx_cnt, width=bar_width, label='Phoenix')
#pl.axhline(res_aegis_alg, linestyle='--', color='m', label='AEGIS')
#pl.axhline(res_random, linestyle=':', color='gray', label='Random')
pl.ylabel('Number of relevant abstracts', fontsize=14)
pl.gca().set_xticks(x)
pl.gca().set_xticklabels(mpf_yrs, rotation='vertical')
tick_spacing = 3
#pl.gca().xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
#pl.gca().xaxis.set_minor_locator(ticker.MultipleLocator(1))
pl.yticks(fontsize=14)
pl.xticks(fontsize=14)
#pl.legend(loc='lower center', fontsize=14)
pl.legend(fontsize=14)
all_file = 'all-by-year.pdf'
pl.savefig(all_file, bbox_inches='tight')
print('Saved joint histogram to %s' % all_file)
