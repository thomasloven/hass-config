from entities import Entities

class OutsideLights(Entities):
    def initialize(self):
        super().initialize()
        for l in self.args['lights']:
            self.register_entity(l, l)

        self.listen_event(self.update, 'TOD_TOD')
        self.listen_event(self.update, 'TOD_DARK')
        self.run_in(lambda *_: self.update(None, None, None), 2)

    def update(self, event, data, kwarg):
        state = self.get_app('timeofday').dark
        if self.get_app('timeofday').tod == 'night':
            state = False

        self.log(f"OUTSIDE LIGHTS - Turning lights {state}")
        for l in self.e:
            self.e[l].state = state
            self.e[l].push()

class DecorativeLights(OutsideLights):
    def update(self, event, data, kwarg):
        state = self.get_app('timeofday').dark
        self.log(f"DECOATIVE LIGHTS - Turning lights {state}")
        for l in self.e:
            self.e[l].state = state
            self.e[l].push()

