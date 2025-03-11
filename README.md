# FourMind

An implementation of a LLM-powered Bot designed for the [TuringGame](https://www.turinggame.ai/). This implementation is based on the [TuringBotClient](https://github.com/SCCH-Nessler/TuringBotClient) library and leverages the [Four-Sides Model](https://en.wikipedia.org/wiki/Four-sides_model) from Friedemann Schulz von Thun.

## Patches

In order to use the TuringBotClient library, you need to apply the following patches to the library:
- Remove the signal handler in `TuringBotClient.py`,
- Change the return type of `async_on_message` to `str | None` in `TuringBotClient.py`
- Remove the `extra-headers` parameter from the websocket connection in `TuringBotClient.py`
