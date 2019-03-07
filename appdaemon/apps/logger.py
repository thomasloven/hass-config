from base import Base

class Logger(Base):
    def initialize(self):
        super().initialize()

        self.listen_event(self.event)
        self.listen_state(self.state)
        self.log_out("Appdaemon logger started")

    def log_out(self, message):
        self.call_service('notify/discord_log', message=message)

    def event(self, name, data, kwargs):
        if name == 'call_service' and data['service'] == 'discord_log':
            return
        self.log_out("EVENT: {} {}".format(name, data))

    def state(self, entity, attribute, old, new, kwargs):
        tracked_domains = ['light', 'switch', 'device_tracker', 'binary_sensor']
        domain = entity.split('.')[0]
        if domain in tracked_domains:
            self.log_out("STATE: {} {} {} =>{}".format(entity, attribute, old, new))
