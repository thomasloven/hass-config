import base
import entities

class HelloWorld(entities.Entities, base.Timers):

    def initialize(self):
        super().initialize()

        self.log("Hello from AppDaemon")
        self.log("You are now ready to run Apps!")

        self.run_in('test1', self.after_time, 3)
        self.run_in('test2', self.after_time2, 7)
        # self.run_in(self.after_time2, 7)
        # self.cancel_timer('test2')

        self.register_entity('taklampa', 'light.kontoret')
        self.e['taklampa'].listen(self.light_changes)

        self.register_entity('dark', 'switch.tod2', True, "on", {
            'icon': 'mdi:lightbulb',
            'friendly_name': 'TEST'})
        self.e['dark'].listen(self.switch)

    def switch(self, old, new, kwarg):
        self.log(f"Switch switched {self.e['dark'].state}")

    def light_changes(self, old, new, kwarg):
        self.log("Light changed!")
        self.log(f"State is {self.e['taklampa'].state}")

    def after_time(self, kwargs):
        self.log("Running function")
        self.e['taklampa'].attr['icon'] = "mdi:lamp"
        # self.e['taklampa'].state = "off"
        self.e['taklampa'].push()
        self.log(f"State is {self.e['taklampa'].state}")
    def after_time2(self, kwargs):
        self.log("Running function2")
        self.e['taklampa'].attr.pop('icon')
        # self.e['taklampa'].state = "on"
        self.e['taklampa'].push()

        self.log(f"State is {self.e['taklampa'].state}")
