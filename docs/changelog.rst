Changelog
*********

- 0.2.4 (2018-04-05)

    * Class :class:`TaskBase`, which is the base class of :class:`ORMTask` and other task classes,
     now has a method to easily build a single task with luigi. For example:

    .. code-block:: python

        class MyTask(ORMTask):

            p1 = luigi.Parameter()

            def run(self):
                # do something ...

        MyTask(p1='foo').build()


    * Added option to disable logging from web request cache
    * Added string sanitation function :func:`etl.util.sanitize`

- 0.2.3 (2018-01-05)

    * New example project 'leonardo'
    * Added option to color pipeline flowchart by task completion status
    * Raise error on pipeline failure in examples



- 0.2.2 (2017-11-28)

    * Fixed order for recursively clearing tasks
    * Improved tests
    * Minor documentation fixes


- 0.2.1 (2017-08-27)

    * Minor fixes in documentation and package release


- 0.2 (2017-08-19)

    * First public release