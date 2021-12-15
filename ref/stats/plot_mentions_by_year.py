# Plot the number of relevant documents (or mentions) per year
# Kiri Wagstaff
# 9/13/20
import pylab as pl
import matplotlib.ticker as ticker
import numpy as np

def plot_hist(yrs, cnt, mission, short_mission):
    pl.clf()
    pl.bar(yrs, cnt)
    pl.xlabel('Year')
    pl.ylabel('Mentions of %s targets' % mission)
    out_fn = '%s-targets-by-year.pdf' % short_mission
    pl.savefig(out_fn, bbox_inches='tight')
    print('Saved %s histogram to %s' % (short_mission, out_fn))

mpf_yrs = range(1998, 2021)
# Obtained from
# cd /proj/mte/results/mpf-reviewed/
# Mentions:
# grep "Target " *ann | cut -f1 -d'_' | uniq -c
mpf_cnt = [201,132,73,29,21,1,2,3,3,0,0,0,0,0,0,2,0,0,0,0,0,0,0]
plot_hist(mpf_yrs, mpf_cnt, 'Pathfinder', 'mpf')

phx_yrs = range(2009, 2021)
# Obtained from
# cd /proj/mte/results/phx-reviewed/
# Mentions:
# grep "Target " *ann | cut -f1 -d'_' | uniq -c
phx_cnt = [177,11,64,27,19,2,13,0,47,43,1,0]
plot_hist(phx_yrs, phx_cnt, 'Phoenix', 'phx')

mera_yrs = range(2004, 2021)
# Obtained from
# cd /proj/mte/results/mer-a-reviewed+properties-v2/
# Mentions:
# grep "Target " *ann | cut -f1 -d'_' | uniq -c
mera_cnt = [26,265,449,514,654,178,282,252,155,148,159,64,63,57,30,27,34]
plot_hist(mera_yrs, mera_cnt, 'MER-A', 'mera')

# Joint plot
pl.clf()
#width = 0.5
width = 0.9
bar_width = width - 0.05
shift = 0.23
#shift = 0.4
x = np.arange(len(mpf_yrs))
#pl.bar(x - shift, mpf_cnt, width=bar_width, label='Pathfinder')
#pl.bar(x[phx_yrs[0] - mpf_yrs[0]:] + shift, phx_cnt, width=bar_width, label='Phoenix')
pl.bar(x[mera_yrs[0] - mpf_yrs[0]:], mera_cnt, 
       width=bar_width, label='MER-A', color='tab:green', alpha=0.8)
pl.bar(x[phx_yrs[0] - mpf_yrs[0]:], phx_cnt, 
       width=bar_width, label='Phoenix', color='tab:orange', alpha=0.8)
pl.bar(x, mpf_cnt, 
       width=bar_width, label='Pathfinder', color='tab:blue', alpha=0.8)
pl.ylabel('Number of target mentions', fontsize=14)
#pl.gca().set_xticks(x)
#pl.gca().set_xticklabels(mpf_yrs, rotation='vertical')
pl.gca().set_xticks(x[::2])
pl.gca().set_xticklabels(mpf_yrs[::2], rotation=45)
tick_spacing = 3
#pl.gca().xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
#pl.gca().xaxis.set_minor_locator(ticker.MultipleLocator(1))
pl.yticks(fontsize=14)
pl.xticks(fontsize=12)
#pl.legend(loc='lower center', fontsize=14)
pl.legend(fontsize=14)
all_file = 'all-targets-by-year.pdf'
pl.savefig(all_file, bbox_inches='tight')
print('Saved joint histogram to %s' % all_file)
