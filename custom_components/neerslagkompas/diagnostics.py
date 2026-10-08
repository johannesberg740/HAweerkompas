"""Privacy-preserving diagnostics, never export secrets or exact coordinates."""


async def async_get_config_entry_diagnostics(hass, entry):
    return {
        "entry": entry.title,
        "version": entry.version,
        "sources": {
            name: {
                "last_update_success": coord.last_update_success,
                "has_fresh_data": coord.current() is not None,
                "points": len(coord.data.points) if coord.data else 0,
            }
            for name, coord in entry.runtime_data.items()
        },
    }
