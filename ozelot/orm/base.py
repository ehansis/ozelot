"""This module defines and instantiates an extended declarative base class for ORM objects.

Attributes:

    Base (ExtendedBase): Instance of extended declarative base class; derive your models from this.

    model_registry (dict): Registry of all model classes derived from the base, key = class name, value = class

Define derived classes like this::

    from sqlalchemy import Column, Integer
    from ozelot.models import base

    class MyModel(base.Base):
        my_field = Column(Integer())
"""
import os
from builtins import object

from sqlalchemy import Column, Integer, func
from sqlalchemy.ext.declarative import declared_attr, DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base

from ozelot import config

model_registry = {}


class RegistryMeta(DeclarativeMeta):
    """Metaclass that registers all objects derived from the base class with the model registry

    Exclude the base class instance itself from the registration.
    """

    # noinspection PyInitNewSignature
    def __init__(cls, name, bases, class_dict):
        if cls.__name__ not in model_registry and cls.__name__ != 'Base':
            model_registry[cls.__name__] = cls
        super(RegistryMeta, cls).__init__(name, bases, class_dict)


class ExtendedBase(object):
    # noinspection PyUnresolvedReferences
    """Extension for :mod:`sqlalchemy` ORM base class.

        Most methods of this class could be class methods. However, the :mod:`sqlalchemy`
        ``@declared_attr`` seems to not play nice with the ``@classmethod`` decorator.
        Methods like :meth`create` or :meth:`drop` have to be called with instance of the
        respective derived model class.

        Attributes:
            __tablename__ (str): Default table name equalling the lower-cased class name
        """

    #: Default integer primary key column
    id = Column(Integer, primary_key=True)

    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    def create_table(self, client):
        """Create the database table belonging to the model.

        If the table already exists, :mod:`sqlalchemy` will throw an error.

        Args:
            client (ozelot.client.Client): database client to use
        """
        # noinspection PyUnresolvedReferences
        self.__table__.create(bind=client.get_engine())

    def drop_table(self, client):
        """Drop the database table belonging to the model

        This will fail if any table row id is still being referenced as a foreign key from another table,
        and if the database backend enforces foreign key constraints (SQLite does not).

        Args:
            client (ozelot.client.Client): database client to use
        """
        # noinspection PyUnresolvedReferences
        self.__table__.drop(bind=client.get_engine())

    @classmethod
    def create_all(cls, client):
        """Create all tables derived from this base class

        Before you call this, import all modules that define the models that you want to create
        tables for (this registers your models with the base class metadata object).

        Args:
            client (ozelot.client.Client): database client to use
        """
        # noinspection PyUnresolvedReferences
        cls.metadata.create_all(bind=client.get_engine())

    @classmethod
    def drop_all(cls, client):
        """Drop all tables derived from this base class

        Before you call this, import all modules that define the models that you want to drop
        tables for (this registers your models with the base class metadata object).

        Args:
            client (ozelot.client.Client): database client to use
        """
        # noinspection PyUnresolvedReferences
        cls.metadata.drop_all(bind=client.get_engine())

    @classmethod
    def get_max_id(cls, session):
        """Get the current max value of the ``id`` column.

        When creating and storing ORM objects in bulk, :mod:`sqlalchemy` does not automatically
        generate an incrementing primary key ``id``. To do this manually, one needs to know the
        current max ``id``. For ORM object classes that are derived from other ORM object classes,
        the max ``id`` of the lowest base class is returned. This is designed to be used with
        inheritance by joining, in which derived and base class objects have identical ``id`` values.

        Args:
            session: database session to operate in
        """
        # sqlalchemy allows only one level of inheritance, so just check this class and all its bases
        id_base = None
        for c in [cls] + list(cls.__bases__):
            for base_class in c.__bases__:
                if base_class.__name__ == 'Base':
                    if id_base is None:
                        # we found our base class for determining the ID
                        id_base = c
                    else:
                        raise RuntimeError("Multiple base object classes for class " + cls.__name__)

        # this should never happen
        if id_base is None:
            raise RuntimeError("Error searching for base class of " + cls.__name__)

        # get its max ID
        max_id = session.query(func.max(id_base.id)).scalar()

        # if no object is present, None is returned
        if max_id is None:
            max_id = 0

        return max_id

    def truncate_to_field_length(self, field, value):
        """Truncate the value of a string field to the field's max length.

        Use this in a validator to check/truncate values before inserting them into the database.
        Copy the below example code after ``@validates`` to your model class and replace ``field1`` and ``field2`` with
        your field name(s).

        :Example:

            from sqlalchemy.orm import validates
            # ... omitting other imports ...

            class MyModel(base.Base):

                field1 = Column(String(128))
                field2 = Column(String(64))

                @validates('field1', 'field2')
                def truncate(self, field, value):
                    return self.truncate_to_field_length(field, value)

        Args:
            field (str): field name to validate
            value (str/unicode): value to validate

        Returns:
            str/unicode: value truncated to field max length

        """
        max_len = getattr(self.__class__, field).prop.columns[0].type.length
        if value and len(value) > max_len:
            return value[:max_len]
        else:
            return value


Base = declarative_base(cls=ExtendedBase, metaclass=RegistryMeta)


def render_diagram(out_base):
    """Render a data model diagram

    Included in the diagram are all classes from the model registry.
    For your project, write a small script that imports all models that you would like to
    have included and then calls this function.

    .. note:: This function requires the 'dot' executable from the GraphViz package to be installed
              and its location configured in your `project_config.py` variable :attr:`DOT_EXECUTABLE`.

    Args:
        out_base (str): output base path (file endings will be appended)
    """
    import codecs
    import subprocess
    import sadisplay

    # generate class descriptions
    desc = sadisplay.describe(list(model_registry.values()),
                              show_methods=False,
                              show_properties=True,
                              show_indexes=True,
                              )

    # write description in DOT format
    with codecs.open(out_base + '.dot', 'w', encoding='utf-8') as f:
        f.write(sadisplay.dot(desc))

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
