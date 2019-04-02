ev = data.get('event', None)
ev_data = data.get('data', {})
if ev:
    hass.bus.fire(ev, ev_data)
