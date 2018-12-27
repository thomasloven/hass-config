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

        functions = [ 'run_in', 'run_once', 'run_at', 'run_daily',
                'run_hourly', 'run_minutely', 'run_every', 'run_at_sunrise',
                'run_at_sunset' ]
        for f in functions:
            self.override(f)

        setattr(self, '_cancel_timer', super().cancel_timer)

    def cancel_timer(self, name, *args, **kwargs):
        if type(name) is str:
            if name in self._timers:
                return super().cancel_timer(self._timers[name])
        else:
            return super().cancel_timer(*args, **kwargs)

    def override(self, f):
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

    def register_entity(self, name, entity):
        domain, _ = entity.split('.')
        controller = {
                'light': Entities.LightEntity,
                }.get(domain, Entities.Entity)
        self.e[name] = controller(self, entity)

    class Entity:
        def __init__(self, hass, entity):
            self._entity = entity
            self._hass = hass
            self._hass.listen_state(self._listener, entity=entity, attributes='all')
            self._listeners = []


        def _listener(self, entity, attribute, old, new, kwargs):
            for l in self._listeners:
                l['callback'](l['kwarg'])
        def listen(self, callback, kwarg=None):
            self._listeners.append({'callback': callback, 'kwarg': kwarg})
            return self._listeners[-1]
        def unlisten(self, handle):
            if handle in self._listeners:
                self._listeners.remove(handle)

        @property
        def state(self):
            return self._hass.get_state(self._entity)
        @state.setter
        def state(self, state):
            self._hass.set_state(self._entity, state=state)

        def __getattr__(self, key):
            return self._hass.get_state(self._entity, attribute='all')['attributes'].get(key, None)
        def __setattr__(self, key, value):
            if key.startswith('_'):
                self.__dict__[key] = value
                return
            d = self._hass.get_state(self._entity, attribute='all')['attributes']
            d[key] = value
            self._hass.set_state(self._entity, attributes=d)
        def __delattr__(self, key):
            if key.startswith('_'):
                del self.__dict__[key]
                return
            d = self._hass.get_state(self._entity, attribute='all')['attributes']
            d[key] = ''
            self._hass.set_state(self._entity, attributes=d)

    class LightEntity(Entities.Entity):
        def __init__(self, hass, entity):
            hass.log("Adding a light")
            super().__init__(hass, entity)
        @property
        def state(self):
            return super().state
        @state.setter
        def state(self, state):
            if state == 'on':
                self._hass.call_service('light/turn_on', entity_id = self._entity)
            elif state == 'off':
                self._hass.call_service('light/turn_off', entity_id = self._entity)
            else:
                return
            super(Entities.LightEntity, self.__class__).state.fset(self, state)
