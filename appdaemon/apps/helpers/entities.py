import base

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


class Entity:

    def __init__(self, hass, entity, managed=False, state=None, attributes=None):
        self._hass = hass
        self._entity = entity
        self._managed = managed
        self._state = state
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
            self._laststate = new
            self._callback(old, new)

    def _callback(self, old, new):
        for l in self._listeners:
            l['callback'](old, new, l['kwarg'])
        pass

    # Updating state
    def pull(self):
        d = self._hass.get_state(self._entity, attribute='all')
        self._state = d['state']
        self._laststate = self._state
        self._attributes = d['attributes']

    def push(self):
        self._hass.set_state(self._entity, state=self._state, attributes=self._attributes)
        if self._state != self._laststate:
            old = self._laststate
            new = self._state
            self._laststate = new
            self.set_state(old, new)
            self._callback(old, new)

    def set_state(self, old, new):
        pass

    # If the entity is controller by appd, changes made in the GUI will be communicated via service calls
    def _service_listener(self, event, data, kwarg):
        if data['service_data'].get('entity_id', '') == self._entity:
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
        if new == "on":
            self._hass.call_service("light/turn_on", entity_id = self._entity)
        elif new == "off":
            self._hass.call_service("light/turn_off", entity_id = self._entity)


class SwitchEntity(Entity):

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
