import os
import json
import base

class EntityManager(base.Base):
    ENTITY_FILE = 'entities.json'

    def initialize(self):
        statedir = os.path.dirname(os.path.realpath(__file__))
        self.statefile = os.path.join(statedir, self.ENTITY_FILE)

        if not os.path.exists(self.statefile):
            os.mknod(self.statefile)
            self.db = {}
        else:
            with open(self.statefile) as f:
                self.db = json.load(f)
        self.get = self.db.get

    def terminate(self):
        with open(self.statefile, 'w') as f:
            json.dump(self.db, f)

    def __getitem__(self, key):
        return self.db.get(key, None)
    def __setitem__(self, key, value):
        self.db[key] = value

class Entities(base.Base):

    def initialize(self):
        if(getattr(super(), 'initialize', False)):
            super().initialize()
        self.e = {}

    def register_entity(self, name, entity, managed=False, default=None, attributes=None):
        domain, _ = entity.split('.')
        controller = {
                'light': LightEntity,
                'switch': SwitchEntity,
                'input_number': InputNumberEntity,
                'input_datetime': InputDateTimeEntity,
                'input_select': InputSelectEntity,
                }.get(domain, Entity)
        self.e[name] = controller(self, entity, managed, default, attributes)
        return self.e[name]


class Entity:

    def __init__(self, hass, entity, managed=False, state=None, attributes=None):
        self._hass = hass
        self.entity_id = entity
        self.domain, self.name = entity.split('.')
        self._managed = managed
        manager = hass.get_app('entity_manager') if managed else {}
        self.manager = manager
        self._state = manager.get(entity, state)
        self._laststate = None
        self._attributes = attributes
        self._listeners = []

        hass.listen_state(self._listener, entity=entity, attribute='all')

        if managed:
            self.push()
            hass.listen_event(self._service_listener, event = 'call_service')
        else:
            self.pull()

    # State change listeners
    def listen(self, callback, kwarg=None):
        self._listeners.append({
            'callback': callback,
            'kwarg': kwarg,
            })
        return self._listeners[-1]

    def unlisten(self, handle):
        if handle in self._listeners:
            self._listeners.remove(handle)

    def _listener(self, entity, attribute, old, new, kwargs):
        self._state = new['state']
        self._attributes = new['attributes']
        old, new = self._laststate, self._state
        if old != new:
            self.manager[self.entity_id] = self._state
            self._laststate = new
            self._callback(old, new)

    def _callback(self, old, new):
        for l in self._listeners:
            l['callback'](old, new, l['kwarg'])
        pass

    # Updating state
    def pull(self):
        d = self._hass.get_state(self.entity_id, attribute='all')
        self._state = d['state']
        self.manager[self.entity_id] = self._state
        self._laststate = self._state
        self._attributes = d['attributes']

    def push(self):
        if self._state != self._laststate:
            self.set_state(self._laststate, self._state)
            self._laststate = self._state
            self._callback(self._laststate, self._state)
        self._hass.set_state(self.entity_id, state=self._state, attributes=self._attributes)
        self.manager[self.entity_id] = self._state

    def set_state(self, old, new):
        pass

    # If the entity is controller by appd, changes made in the GUI will be communicated via service calls
    def _service_listener(self, event, data, kwarg):
        if data['service_data'].get('entity_id', '') == self.entity_id:
            self.service_callback(data)

    def service_callback(self, data):
        pass

    #
    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, value):
        self._state = value

    @property
    def attr(self):
        return self._attributes


class LightEntity(Entity):

    def set_state(self, old, new):
        if new == "on" or new == True:
            self._hass.call_service("light/turn_on", entity_id = self.entity_id)
            self._state = "on"
        elif new == "off" or new == False:
            self._hass.call_service("light/turn_off", entity_id = self.entity_id)
            self._state = "off"


class SwitchEntity(Entity):

    def set_state(self, old, new):
        if new == "on" or new == True:
            self._hass.call_service("switch/turn_on", entity_id = self.entity_id)
            self._state = "on"
        if new == "off" or new == False:
            self._hass.call_service("switch/turn_off", entity_id = self.entity_id)
            self._state = "off"

    def service_callback(self, data):
        if data['service'] == 'turn_on':
            self._state = "on"
        if data['service'] == 'turn_off':
            self._state = "off"
        self.push()


class InputNumberEntity(Entity):

    def service_callback(self, data):
        if data['domain'] == 'input_number' and data['service'] == 'set_value':
            self._state = data['service_data']['value']
            self.push()

class InputDateTimeEntity(Entity):

    def set_state(self, old, new):
        time = new.split(':')
        time += ["00"] * (3 - len(time))
        self._state = ':'.join(time)
        self.attr['hour'] = int(time[0], base=10)
        self.attr['minute'] = int(time[1], base=10)
        self.attr['seconf'] = int(time[2], base=10)

    def service_callback(self, data):
        if data['service'] == 'set_datetime':
            self._state = data['service_data'].get('time', "00:00:00")
            self.push()

class InputSelectEntity(Entity):

    def service_callback(self, data):
        if data['service'] == 'select_option':
            self._state = data['service_data'].get('option', None)
            self.push()
