from abc import ABC, abstractmethod

_ACTION_CONTROLLER = None


class ActionController(ABC):
    """
    Controller of actions to be performed at certain times.
    """

    @abstractmethod
    async def on_action(self):
        """
        Turning on action.
        """

    @abstractmethod
    async def off_action(self):
        """
        Turning off action.
        """


def set_global_action_controller(action_controller: ActionController):
    """
    Sets the single global action controller.
    :param action_controller: action controller to set
    """
    global _ACTION_CONTROLLER
    _ACTION_CONTROLLER = action_controller


def get_global_action_controller() -> ActionController:
    """
    Gets the single global action controller.
    :returns: global action controller
    """
    return _ACTION_CONTROLLER
