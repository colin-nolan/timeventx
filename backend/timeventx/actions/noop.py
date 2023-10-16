from timeventx.actions.actions import ActionController, set_global_action_controller


class NoopActionController(ActionController):
    """
    Action controller implementation that does nothing.
    """

    async def on_action(self):
        pass

    async def off_action(self):
        pass


set_global_action_controller(NoopActionController())
