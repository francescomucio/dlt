import os
import tomlkit

from dlt.common.configuration.container import Container
from dlt.common.configuration.providers.toml import ConfigTomlProvider
from dlt.common.configuration.specs import RunConfiguration

from dlt.cli import echo as fmt
from dlt.cli.utils import get_telemetry_status
from dlt.cli.config_toml_writer import WritableConfigValue, write_values
from dlt.common.configuration.specs.config_providers_context import ConfigProvidersContext
from dlt.common.runtime.anon_tracker import get_anonymous_id

DLT_TELEMETRY_DOCS_URL = "https://dlthub.com/docs/reference/telemetry"


def telemetry_status_command() -> None:
    if get_telemetry_status():
        fmt.echo("Telemetry is %s" % fmt.bold("ENABLED"))
        fmt.echo("Anonymous id %s" % fmt.bold(get_anonymous_id()))
    else:
        fmt.echo("Telemetry is %s" % fmt.bold("DISABLED"))


def change_telemetry_status_command(enabled: bool) -> None:
    # value to write
    telemetry_value = [
        WritableConfigValue("dlthub_telemetry", bool, enabled, (RunConfiguration.__section__,))
    ]
    # write local config
    # TODO: use designated (main) config provider (for non secret values) ie. taken from run context
    config = ConfigTomlProvider(add_global_config=False)
    if not config.is_empty:
        write_values(config._config_toml, telemetry_value, overwrite_existing=True)
        config.write_toml()

    # write global config
    from dlt.common.runtime import run_context

    global_path = run_context.current().global_dir
    os.makedirs(global_path, exist_ok=True)
    config = ConfigTomlProvider(settings_dir=global_path, add_global_config=False)
    write_values(config._config_toml, telemetry_value, overwrite_existing=True)
    config.write_toml()

    if enabled:
        fmt.echo("Telemetry switched %s" % fmt.bold("ON"))
    else:
        fmt.echo("Telemetry switched %s" % fmt.bold("OFF"))
    # reload config providers
    if ConfigProvidersContext in Container():
        del Container()[ConfigProvidersContext]
