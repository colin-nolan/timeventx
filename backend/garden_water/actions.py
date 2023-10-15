from abc import ABC, abstractmethod

_ACTION_CONTROLLER = None


class ActionController(ABC):
    """
    TODO
    """

    @abstractmethod
    async def on_action(self):
        """
        TODO
        """

    @abstractmethod
    async def off_action(self):
        """
        TODO
        """


class NoopActionController(ABC):
    async def on_action(self):
        pass

    async def off_action(self):
        pass


def set_action_controller(action_controller: ActionController):
    """
    TODO
    """
    global _ACTION_CONTROLLER
    _ACTION_CONTROLLER = action_controller


def get_action_controller() -> ActionController:
    """
    TODO
    """
    return _ACTION_CONTROLLER
