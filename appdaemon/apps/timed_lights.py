from entities import Entities

class OutsideLights(Entities):
    def initialize(self):
        super().initialize()
        for l in self.args['lights']:
            e = self.register_entity(l, l)
            e.listen(self.found, {'entity': e})


        self.listen_event(self.update, 'TOD_TOD')
        self.run_in(lambda *_: self.update(None, None, None), 2)

    def update(self, event, data, kwarg):
        self.state = self.get_app('timeofday').dark
        if self.get_app('timeofday').tod == 'night':
            self.state = False

        self.log(f"OUTSIDE LIGHTS - Turning lights {self.state}")
        for l in self.e:
            self.e[l].state = self.state
            self.e[l].push()

    def found(self, old, new, kwarg):
        entity = kwarg.get('entity', None)
        if not entity: return;

        if old == "unavailable":
            self.log(f"{entity.entity_id} showed up, setting to {self.state}")
            entity.state = self.state
            entity.push()

class DecorativeLights(OutsideLights):
    def update(self, event, data, kwarg):
        self.state = self.get_app('timeofday').dark
        self.log(f"DECORATIVE LIGHTS - Turning lights {self.state}")
        for l in self.e:
            self.e[l].state = self.state
            self.e[l].push()

