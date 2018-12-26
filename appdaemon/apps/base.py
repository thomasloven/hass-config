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

