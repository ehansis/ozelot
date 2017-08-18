"""Target classes for :mod:`luigi`."""
from builtins import str

import datetime

from sqlalchemy import Column, String, DateTime

from ozelot.orm import base


class ORMTargetMarker(base.Base):
    # noinspection PyUnresolvedReferences
    """ORM object class to store task completion markers.
    """

    #: *Column(String)*: target name, usually equals name of the associated task
    name = Column(String())

    #: *Column(String)*: string representation of task parameters
    params = Column(String())

    #: *Column(DateTime)*: Time stamp for object creation
    created = Column(DateTime, default=datetime.datetime.utcnow)

    def __str__(self):
        return self.name + " " + self.params + " " + str(self.created)
