from entities import Entities

class Vacuum(Entities):
    def initialize(self):
        super().initialize()
        self.entity_id = self.args['entity_id']

        self.run_in(self._setup, 1)

    def _setup(self, kwargs):
        for zone in self.args['zones']:
            e = dict(self.args['zones'][zone])
            name = f'switch.vacuum_{zone}'
            self.register_entity(zone, name, True, "off", e)

        self.listen_event(self.zone, 'VACUUM_ZONE')
        self.listen_event(self.all, 'VACUUM_ALL')
        self.listen_event(self.service, 'VACUUM_SERVICE')
        self.listen_event(self.home, 'VACUUM_HOME')

    def zone(self, ev, data, kwargs):
        areas = []
        for zone in self.args['zones']:
            if self.e[zone].state == "on":
                areas.append(self.e[zone].attr['area'])

        self.call_service("vacuum/xiaomi_clean_zone", repeats = 1, zone = areas)

    def all(self, ev, data, kwargs):
        self.call_service("vacuum/start")
    def service(self, ev, data, kwargs):
        self.call_service("vacuum/send_command", entity_id = self.entity_id, command = 'app_goto_target', params = self.args['empty_spot'])
    def home(self, ev, data, kwargs):
        self.call_service("vacuum/return_to_base", entity_id = self.entity_id)
