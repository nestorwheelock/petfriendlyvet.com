"""EMR service functions.

All EMR business logic lives here. Views call these functions.
No direct model .save() calls from views.
"""
from . import encounters
from . import events

__all__ = ['encounters', 'events']
