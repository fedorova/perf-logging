#!/usr/bin/env python

import pandas as pd
import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show, output_file


# setup range
rng = pd.date_range(start='3/11/16', periods=48, freq='H' )
td = pd.Series([ pd.Timedelta(minutes=i) for i in np.random.randint(0,59,48) ])

interval = pd.DataFrame({'start' : rng })
interval['end'] = interval['start'] + td

print "This is td:";
print td;

print "This is start:";
print interval['start'];

print "This is end:";
print interval['end'];


cds_df = ColumnDataSource(interval)

p = figure(x_axis_type='datetime', plot_height=100, plot_width=500, responsive=True)

# hide the toolbar
p.toolbar_location=None

# formatting
p.yaxis.minor_tick_line_color = None
p.ygrid[0].ticker.desired_num_ticks = 1

y1 = p.quad(left='start',right='end',bottom=0, top=1, source=cds_df )

output_file("time_interval.html", mode='cdn')
show(p)
