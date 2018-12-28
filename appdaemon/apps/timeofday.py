import base
class TimeOfDay(base.Entities):
    def initialize(self):
        super().initialize()

        self.run_in(self.setup_inputs, 1)

    def setup_inputs(self, kwargs):
        inputs = ['morning', 'day', 'evening', 'night', 'sunrise', 'sunset', 'tod', 'dark']
        for i in inputs:
            e = dict(self.args[i])
            name = e['name']
            default = e['default']
            del e['name']
            del e['default']
            self.register_entity(i, name, True, default, e)

        self.e['sunrise'].listen(self.input_listener, {'changed': "sunrise"})


    def input_listener(self, kwargs):
        self.log(kwargs)
