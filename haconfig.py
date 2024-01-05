# haconfig.py

version = (1, 0, 0)

# used to generate config json for homeassistant

import json

haconfig_topic = "homeassistant/{}/config"

def haconfig_msg(entity, units) -> str:
	name = entity[entity.index("/")+1:]
	topic = "hass/{}".format(entity)
	msg = { "~": topic, "name": name, 'uniq_id': name, 'obj_id': name, 'stat_t': "~/state",
			'json_attr_t': "~/attrs", "retain": True }
	if units:
		msg['unit_of_meas'] = units

	if '/switch/' in entity:
		msg['cmd_t'] = "~/set"

	if '/cover/' in entity:
		msg['cmd_t'] = "~/set"
		msg['pos_t'] = "~_position/state"

	if '/light/' in entity:
		msg['cmd_t'] = "~/set"
		msg['bri_cmd_t'] = "~_bri/set"
		msg['bri_stat_t'] = "~_bri/state"
		msg['rgb_cmd_t'] = "~_rgb/set"
		msg['rgb_stat_t'] = "~_rgb/state"
			
	return json.dumps(msg)
