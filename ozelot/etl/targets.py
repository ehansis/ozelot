from builtins import object
from ozelot import client
from ozelot.orm.target import ORMTargetMarker


class ORMTarget(object):
    """Pipeline target that stores task completion markers in a database, via an ORM layer.
    """

    def __init__(self, name, params):
        """Create a new target instance

        Args:
            name: task name
            params: task parameters
        """
        self.name = name
        self.params = params

    @classmethod
    def from_task(cls, task):
        """Create a new target representing a task and its parameters

        Args:
            task: Task instance to create target for; the task class has to inherit
                from :class:`ozelot.tasks.TaskBase`.

        Returns:
            ozelot.tasks.ORMTarget: a new target instance
        """
        target = cls(name=task.get_name(),
                     params=task.get_param_string())

        return target

    def _base_query(self, session):
        """Base query for a target.

        Args:
            session: database session to query in
        """
        return session.query(ORMTargetMarker) \
            .filter(ORMTargetMarker.name == self.name) \
            .filter(ORMTargetMarker.params == self.params)

    def exists(self):
        """Check if a target exists

        This function is called by :mod:`luigi` to check if a task output exists. By default,
        :mod:`luigi` considers a task as complete if all it targets (outputs) exist.

        Returns:
            bool: ``True`` if target exists, ``False`` otherwise
        """
        # get DB connection
        session = client.get_client().create_session()

        # query for target existence
        ret = self._base_query(session).count() > 0

        session.close()

        return ret

    def create(self):
        """Create an instance of the current target in the database

        If a target with the current name and params already exists, no second instance is created.
        """
        session = client.get_client().create_session()

        if not self._base_query(session).count() > 0:
            # store a new target instance to the database
            marker = ORMTargetMarker(name=self.name,
                                     params=self.params)
            session.add(marker)
            session.commit()

        session.close()

    def remove(self):
        """Remove a target

        Raises a ``RuntimeError`` if the target does not exist.
        """
        session = client.get_client().create_session()

        if not self._base_query(session).count() > 0:
            session.close()
            raise RuntimeError("Target does not exist, name={:s}, params={:s}"
                               "".format(self.name, self.params))

        # remove the target from the database
        self._base_query(session).delete()
        session.commit()

        session.close()
