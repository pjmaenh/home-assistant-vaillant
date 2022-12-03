# home-assistant-vaillant

| :warning: WARNING          |
|:---------------------------|
| This custom component is **not maintained anymore**. However, [@MislavMandaric](https://github.com/MislavMandaric) has completely rewritten the component, and his version can be found at https://github.com/MislavMandaric/home-assistant-vaillant-vsmart.      |



**Home Assistant component for integrating Vaillant vSMART and Bulex/Saunier Duval MiGo**

This component allows you to control a Vaillant vSMART of Bulex/Saunier Duval MiGo through Home Assistant.
The component uses the customized Vaillant [netatmo-api-python library](https://github.com/samueldumont/netatmo-api-python/) developed by Samuel Dumont, and is based on the Home Assistant components [vaillant.py](https://gitlab.com/samueldumont/home-assistant/blob/added_vaillant/homeassistant/components/vaillant.py) and [climate/vaillant.py](https://gitlab.com/samueldumont/home-assistant/blob/added_vaillant/homeassistant/components/climate/vaillant.py) previously developed by the same author.

This project has no relation with the Vaillant/Bulex/Saunier Duval company.

## Installation and Configuration

To install the component, copy the *vaillant* folder from custom_components to the custom_components folder of your Home Assistant instance.

Add the following section to your configuration file (*configuration.yaml*)

```
vaillant:
  api_key: <API_KEY>
  secret_key: <SECRET_KEY>
  username: <USERNAME>
  password: <PASSWORD>
  discovery: False
  app_version: <APP_VERSION>
  user_prefix: <USER_PREFIX>

climate:
  - platform: vaillant
```

Remarks:
- Replace `<USERNAME>` and `<PASSWORD>` by your Vaillant / Bulex / Saunier Duval credentials.
- Replace `<API_KEY>`, `<SECRET_KEY>`, `<APP_VERSION>` and `<USER_PREFIX>` by the correct keys for either Vaillant or Bulex / Saunier Duval. The required values can be retrieved by decompiling the official mobile app.

After restarting your Home Assistant instance, your thermostat(s) should be visible within Home Assistant.
If not, check your Home Assistant log files. When the following error is visible within your log files:
```
TypeError: ‘NoneType’ object is not subscriptable
```
This means that authentication failed. Either your credentials are incorrect, or the combination of `<API_KEY>`, `<SECRET_KEY>`, `<APP_VERSION>` and `<USER_PREFIX>` is wrong.
