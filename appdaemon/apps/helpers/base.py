import appdaemon.plugins.hass.hassapi as hass

class Base(hass.Hass):
    def initialize(self):
        if(getattr(super(), 'initialize', False)):
            super().initialize()
