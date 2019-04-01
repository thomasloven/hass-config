from entities import Entities

class OutsideLights(Entities):
    def initialize(self):
        super().initialize()
        for l in self.args['lights']:
            self.register_entity(l, l)

        self.listen_event(self.update, 'TOD_TOD')
        self.run_in(lambda *_: self.update(None, None, None), 2)
        for l in self.args['lights']:
            self.listen_event(self.found, l, old="unavailable")

    def update(self, event, data, kwarg):
        self.state = self.get_app('timeofday').dark
        if self.get_app('timeofday').tod == 'night':
            self.state = False

        self.log(f"OUTSIDE LIGHTS - Turning lights {self.state}")
        for l in self.e:
            self.e[l].state = self.state
            self.e[l].push()

    def found(self, entity, attribute, old, new, kwargs):
        if old == "unavailable":
            self.log(f"{entity} showed up, setting to {self.state}")
            self.e[entity].state = self.state
            self.e[entity].push()

class DecorativeLights(OutsideLights):
    def update(self, event, data, kwarg):
        self.state = self.get_app('timeofday').dark
        self.log(f"DECORATIVE LIGHTS - Turning lights {self.state}")
        for l in self.e:
            self.e[l].state = self.state
            self.e[l].push()

