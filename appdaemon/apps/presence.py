from entities import Entities
from timers import Timers

class Presence(Timers, Entities):

    HOME = 'home'
    AWAY = 'not_home'
    ARRIVED = 'just_arrived'
    LEFT = 'just_left'
    TIMEOUT = 300

    def initialize(self):
        super().initialize()

        attr = self.args.get('attributes', {})

        self.register_entity('tracker', self.args['name'], managed=True, default="not_home", attributes=self.args.get('attributes',{}))
        self.tracker = self.e['tracker']
        if(self.tracker.state in [self.ARRIVED, self.LEFT]):
            self.tracker.state = self.AWAY

        self.devices = []
        for i,d in enumerate(self.args['devices']):
            name = f"device{i}"
            self.register_entity(name, d);
            self.e[name].listen(self.update, {"name": name})
            self.devices.append(self.e[name])

        self.update()

    def update(self, old=None, new=None, kwarg=None):
        if not old or isinstance(old, str):
            timeout = False
        elif old is None:
            timeout = False
        else:
            timeout = old.get('trigger', False)
        new_state = self.is_home()
        old_state = self.tracker.state
        if new_state:
            if old_state == self.AWAY:
                self.run_in('timeout', self.update, self.TIMEOUT, trigger = "timeout")
                state = self.ARRIVED
            elif old_state == self.LEFT:
                self.cancel_timer('timeout')
                state = self.HOME
            elif old_state == self.ARRIVED and timeout:
                state = self.HOME
            else:
                state = old_state
        else:
            if old_state == self.HOME:
                self.run_in('timeout', self.update, self.TIMEOUT, trigger = "timeout")
                state = self.LEFT
            elif old_state == self.ARRIVED:
                self.cancel_timer('timeout')
                state = self.AWAY
            elif old_state == self.LEFT and timeout:
                state = self.AWAY
            else:
                state = old_state

        self.tracker.state = state
        self.tracker.push()

    def is_home(self):
        for d in self.devices:
            if d.domain == 'device_tracker':
                if d.attr['source_type'] in ['router']:
                    if d.state == 'home':
                        return True
            if d.domain == 'sensor':
                if d.state != 'unknown' and int(d.state) > 0:
                    return True

        return False



