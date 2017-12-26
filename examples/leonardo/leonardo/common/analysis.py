from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from os import path
import io

import jinja2
import numpy as np
from matplotlib import pyplot as plt
import seaborn

from ozelot import client, config

# global jinja2 environment
jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(path.join(path.dirname(__file__), 'templates')))

# global output directory, default is directory containing this file
out_dir = path.dirname(__file__)


def fig_to_svg(fig):
    """Helper function to convert matplotlib figure to SVG string

    Returns:
        str: figure as SVG string
    """
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    buf.seek(0)
    return buf.getvalue()


def pixels_to_inches(size):
    """Helper function: compute figure size in inches @ 72 dpi

    Args:
        size (tuple(int, int)): figure size in pixels

    Returns:
        tuple(int, int): figure size in inches
    """
    return size[0] / 72., size[1] / 72.


def plots_html_page(query_module):
    """Generate analysis output as html page """

    # page template
    template = jenv.get_template("analysis.html")

    # container for template context
    context = dict(extended=config.EXTENDED)

    # a database client/session to run queries in
    cl = client.get_client()
    session = cl.create_session()

    # general styling
    seaborn.set_style('whitegrid')

    #
    #  plot: painting area by decade, with linear regression
    #

    decade_df = query_module.decade_query()

    pix_size = pixels_to_inches((600, 400))
    ax = seaborn.lmplot(x='decade', y='area', data=decade_df,
                        size=pix_size[1], aspect=pix_size[0] / pix_size[1],
                        scatter_kws={"s": 30, "alpha": 0.3})
    ax.set(xlabel='Decade', ylabel='Area, m^2')
    context['area_by_decade_svg'] = fig_to_svg(plt.gcf())
    plt.close('all')

    #
    #  plot: painting area by gender, with logistic regression
    #

    if config.EXTENDED:
        gender_df = query_module.gender_query()

        pix_size = pixels_to_inches((600, 400))
        g = seaborn.FacetGrid(gender_df, hue="gender", margin_titles=True,
                              size=pix_size[1], aspect=pix_size[0] / pix_size[1])
        bins = np.linspace(0, 5, 30)
        g.map(plt.hist, "area", bins=bins, lw=0, alpha=0.5, normed=True)
        g.axes[0, 0].set_xlabel('Area, m^2')
        g.axes[0, 0].set_ylabel('Percentage of paintings')
        context['area_by_gender_svg'] = fig_to_svg(plt.gcf())
        plt.close('all')

    #
    # render template
    #

    out_file = path.join(out_dir, "analysis.html")
    html_content = template.render(**context)
    with open(out_file, 'w') as f:
        f.write(html_content)

    # done, clean up
    plt.close('all')
    session.close()
