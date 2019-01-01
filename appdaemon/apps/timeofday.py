from datetime import timedelta

from timers import Timers
from entities import Entities
class TimeOfDay(Timers, Entities):

    TOD = ['morning', 'day', 'evening', 'night']

    def initialize(self):
        super().initialize()

        self.run_in(self._setup_inputs, 1)

        self.updating = False

    def _setup_inputs(self, kwargs):
        inputs = [
                'morning',
                'day',
                'evening',
                'night',
                'sunrise',
                'sunset',
                'tod',
                'dark',
                ]
        for i in inputs:
            e = dict(self.args[i])
            name = e['name']
            default = e['default']
            del e['name']
            del e['default']
            self.register_entity(i, name, True, default, e)
        for i in inputs:
            self.e[i].listen(self._update, {'trigger': 'setting', 'entity': i})

        self._update(None, None, {'trigger': 'init'})

    def _update(self, old=None, new=None, kwarg=None):

        if self.updating:
            return

        if kwarg is None:
            kwarg = old
        trigger = kwarg.get('trigger', None)

        self.log(f"TOD - updated by {trigger}")

        # Set up triggers for each TOD
        for t in self.TOD:
            if not trigger == t:
                self.run_once(
                        t,
                        self._update,
                        self.parse_time(self.e[t].state),
                        trigger=t
                        )

        # Set up triggers for sunrise and sunset
        sunrise = float(self.e['sunrise'].state)
        sunrise = timedelta(minutes=sunrise)
        sunrise = (self.sunrise() + sunrise).time()
        if trigger != 'sunrise':
            self.run_once(
                    'sunrise',
                    self._update,
                    sunrise,
                    trigger='sunrise'
                    )
        sunset = float(self.e['sunset'].state)
        sunset = timedelta(minutes=sunset)
        sunset = (self.sunset() + sunset).time()
        if trigger != 'sunset':
            self.run_once(
                    'sunset',
                    self._update,
                    sunset,
                    trigger='sunset'
                    )

        # Determine current time of day
        if trigger in self.TOD:
            tod = trigger
        else:
            tod = 'night'
            for t in self.TOD:
                if self.time() >= self.parse_time(self.e[t].state):
                    tod = t

        # Determine if sun is down
        if trigger == 'sunrise':
            dark = False
        elif trigger == 'sunset':
            dark = True
        elif sunrise <= self.time() <= sunset:
            dark = False
        else:
            dark = True


        self.log(f"TOD - Time of day is {tod}, sun {'has set' if dark else 'is up'}")

        # Update outputs
        self.updating = True
        self.e['dark'].state = dark
        self.e['dark'].push()
        self.e['tod'].state = tod
        self.e['tod'].push()
        self.e['sunrise'].attr['time'] = sunrise.strftime("%H:%M:%S")
        self.e['sunrise'].push()
        self.e['sunset'].attr['time'] = sunset.strftime("%H:%M:%S")
        self.e['sunset'].push()
        self.updating = False

        # Tell listeners if Time Of Day or Dark has changed
        self.fire_event('TOD_TOD', old = old, new = new)

    @property
    def tod(self):
        return self.e['tod'].state
    @property
    def dark(self):
        return self.e['dark'].state == "on"
