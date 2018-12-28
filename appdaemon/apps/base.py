import appdaemon.plugins.hass.hassapi as hass

class Base(hass.Hass):
    def initialize(self):
        if(getattr(super(), 'initialize', False)):
            super().initialize()

class Timers(Base):
    def initialize(self):
        if(getattr(super(), 'initialize', False)):
            super().initialize()
        self._timers = {}

        functions = [
                'run_in',
                'run_once',
                'run_at',
                'run_daily',
                'run_hourly',
                'run_minutely',
                'run_every',
                'run_at_sunrise',
                'run_at_sunset',
                ]
        for f in functions:
            self._override(f)

        setattr(self, '_cancel_timer', super().cancel_timer)

    def cancel_timer(self, name, *args, **kwargs):
        if type(name) is str:
            if name in self._timers:
                return super().cancel_timer(self._timers[name])
        else:
            return super().cancel_timer(*args, **kwargs)

    def _override(self, f):
        setattr(self, f'_{f}', getattr(self, f))
        def fn(name, *args, **kwargs):
            if type(name) is str:
                if name in self._timers:
                    super().cancel_timer(self._timers[name])
                self._timers[name] = getattr(self, f'_{f}')(*args, **kwargs)
                return self._timers[name]
            else:
                return getattr(self, f'_{f}')(name, *args, **kwargs)
        setattr(self, f, fn)

class Entities(Base):
    def initialize(self):
        if(getattr(super(), 'initialize', False)):
            super().initialize()

        self.e = {}

    def register_entity(self, name, entity, managed=False, default=None, attributes=None):
        domain, _ = entity.split('.')
        controller = {
                'light': Entities.LightEntity,
                'input_datetime': Entities.InputDateTimeEntity,
                'input_number': Entities.InputNumberEntity,
                }.get(domain, Entities.Entity)
        self.e[name] = controller(self, entity, managed, default, attributes)

    class Entity:
        def __init__(self, hass, entity, managed = False, default = None, attributes = None):
            self._entity = entity
            self._hass = hass
            self._hass.listen_state(self._listener, entity=entity, attributes='all')
            self._listeners = []
            if managed:
                if default:
                    self.state = default
                self.update(attributes)

        def listen(self, callback, kwarg=None):
            """ Listen to changes to entity state """
            self._listeners.append({
                'callback': callback,
                'kwarg': kwarg,
                })
            return self._listeners[-1]
        def unlisten(self, handle):
            """ Remove state change listener """
            if handle in self._listeners:
                self._listeners.remove(handle)
        def _listener(self, entity, attribute, old, new, kwargs):
            for l in self._listeners:
                l['callback'](l['kwarg'])

        def __getattr__(self, key):
            if key == 'state':
                if self.get_state:
                    return self.get_state()
                return self._hass.get_state(self._entity)
            return self._hass.get_state(self._entity,
                    attribute=key)
        def __setattr__(self, key, value):
            if key.startswith('_'):
                self.__dict__[key] = value
                return
            if key == 'state':
                if self.set_state:
                    self.set_state(value)
                return self._hass.set_state(self._entity, state=value)
            attr = self._hass.get_state(self._entity,
                    attribute='all')
            attr = attr.get('attributes', {}) if attr else {}
            attr[key] = value
            self._hass.set_state(self._entity, attributes=attr)
        def __delattr__(self, key):
            if key.startswith('_'):
                del self.__dict__[key]
                return
            attr = self._hass.get_state(self._entity,
                    attribute='all').get('attributes', {})
            attr[key] = ''
            self._hass.set_state(self._entity, attributes=attr)

        def update(self, new):
            attr = self._hass.get_state(self._entity, attribute='all').get('attributes', {})
            attr.update(new)
            self._hass.set_state(self._entity, attributes=attr)

    class LightEntity(Entities.Entity):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def set_state(self, state):
            if state == 'on':
                self._hass.call_service('light/turn_on', entity_id =
                        self._entity)
            elif state == 'off':
                self._hass.call_service('light/turn_off', entity_id =
                        self._entity)
            else:
                return

    class InputNumberEntity(Entities.Entity):
        def __init__(self, hass, entity, managed = False, default = None, attributes = None):
            super().__init__(hass, entity, managed, default, attributes)
            if managed:
                hass.listen_event(self.service_callback, event = 'call_service')

        def service_callback(self, event, data, kwargs):
            if data['service_data'].get('entity_id', '') == self._entity and data['service'] == 'set_value':
                self._hass.log("Value changed!")


    class InputDateTimeEntity(Entities.Entity):
        def __init__(self, hass, entity, managed = False, default = None, attributes = None):
            super().__init__(hass, entity, managed, default, attributes)
            if managed:
                hass.listen_event(self.service_callback, event = 'call_service')

        def service_callback(self, event, data, kwargs):
            if data['service_data'].get('entity_id', '') == self._entity and data['service'] == 'set_datetime':
                self._hass.log("Datetime changed!")

        def set_state(self, state):
            time = state.split(':')
            time += ['00'] * (3 - len(time))
            self._hass.set_state(self._entity, state=':'.join(time))
            self.update({
                'hour': int(time[0], base=10),
                'minute': int(time[1], base=10),
                'second': int(time[2], base=10),
                })
