import os


"""
Utility functions for ETL pipelines
"""


def render_diagram(root_task, out_base, max_param_len=20, horizontal=False):
    """Render a diagram of the ETL pipeline

    All upstream tasks (i.e. requirements) of :attr:`root_task` are rendered.

    Nodes are, by default, styled as simple rects. This style is augmented by any
    :attr:`diagram_style` attributes of the tasks.

    .. note:: This function requires the 'dot' executable from the GraphViz package to be installed
              and its location configured in your `project_config.py` variable :attr:`DOT_EXECUTABLE`.

    Args:
        root_task (luigi.Task): Task instance that defines the 'upstream root' of the pipeline
        out_base (str): base output file name (file endings will be appended)
        max_param_len (int): Maximum shown length of task parameter values
        horizontal (bool): If True, layout graph left-to-right instead of top-to-bottom
    """
    import re
    import codecs
    import subprocess
    from ozelot import config
    from ozelot.etl.tasks import get_task_name, get_task_param_string

    # the graph - lines in dot file
    lines = [u"digraph G {"]

    if horizontal:
        lines.append(u"rankdir=LR;")

    # helper function: make unique task id from task name and parameters:
    # task name + parameter string, with spaces replaced with _ and all non-alphanumerical characters stripped
    def get_id(task):
        s = get_task_name(task) + "_" + get_task_param_string(task)
        return re.sub(r'\W+', '', re.sub(' ', '_', s))

    # node names of tasks that have already been added to the graph
    existing_nodes = set()

    # edge sets (tuples of two node names) that have already been added
    existing_edges = set()

    # recursion function for generating the pipeline graph
    def _build(task, parent_id=None):
        tid = get_id(task)

        # add node if it's not already there
        if tid not in existing_nodes:
            # build task label: task name plus dictionary of parameters as table

            params = task.to_str_params()
            param_list = ""
            for k, v in params.items():
                # truncate param value if necessary, and add "..."
                if len(v) > max_param_len:
                    v = v[:max_param_len] + "..."
                param_list += "<TR><TD ALIGN=\"LEFT\">" \
                              "<FONT POINT-SIZE=\"10\">{:s}</FONT>" \
                              "</TD><TD ALIGN=\"LEFT\">" \
                              "<FONT POINT-SIZE=\"10\">{:s}</FONT>" \
                              "</TD></TR>".format(k, v)

            label = "<TABLE BORDER=\"0\" CELLSPACING=\"1\" CELLPADDING=\"1\">" \
                    "<TR><TD COLSPAN=\"2\" ALIGN=\"CENTER\">" \
                    "<FONT POINT-SIZE=\"12\">{:s}</FONT>" \
                    "</TD></TR>" \
                    "".format(get_task_name(task)) + param_list + "</TABLE>"

            # add a node for the task
            lines.append(u"{name:s} [label=< {label:s} >, shape=\"rect\", style=\"{style:s}\"];\n"
                         u"".format(name=tid,
                                    label=label,
                                    style=','.join(getattr(task, 'diagram_style', []))))

            existing_nodes.add(tid)

            # recurse over requirements
            for req in task.requires():
                _build(req, parent_id=tid)

        # add edge from current node to (upstream) parent, if it doesn't already exist
        if parent_id is not None and (tid, parent_id) not in existing_edges:
            lines.append(u"{source:s} -> {target:s};\n".format(source=tid, target=parent_id))

    # generate pipeline graph
    _build(root_task)

    # close the graph definition
    lines.append(u"}")

    # write description in DOT format
    with codecs.open(out_base + '.dot', 'w', encoding='utf-8') as f:
        f.write(u"\n".join(lines))

    # check existence of DOT_EXECUTABLE variable and file
    if not hasattr(config, 'DOT_EXECUTABLE'):
        raise RuntimeError("Please configure the 'DOT_EXECUTABLE' variable in your 'project_config.py'")
    if not os.path.exists(config.DOT_EXECUTABLE):
        raise IOError("Could not find file pointed to by 'DOT_EXECUTABLE': " + str(config.DOT_EXECUTABLE))

    # render to image using DOT
    # noinspection PyUnresolvedReferences
    subprocess.check_call([
        config.DOT_EXECUTABLE,
        '-T', 'png',
        '-o', out_base + '.png',
              out_base + '.dot'
    ])
