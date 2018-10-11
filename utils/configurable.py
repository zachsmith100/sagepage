##############
# Configurable
##############
class Configurable:
  def load_config(config, target_obj, matches_only=True):
    if matches_only:
      for key in target_obj.__dict__:
        if key in config:
          setattr(target_obj, key, config[key])
    else:
      for key in config:
        setattr(target_obj, key, config[key])
    return target_obj

  def copy_config(src_obj, target_obj):
    for key in target_obj.__dict__:
      if key in src_obj.__dict__:
        setattr(target_obj, key, getattr(src_obj, key))
    return target_obj

  def overlay_config(target_obj, target_config, target_config_key=None):
    config = target_config
    if target_config_key:
      if target_config_key not in target_config:
        return
      config = target_config[target_config_key]
    return Configurable.load_config(config, target_obj)