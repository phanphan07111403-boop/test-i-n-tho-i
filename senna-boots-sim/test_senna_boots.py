#!/usr/bin/env python3
"""Sanity checks for Senna Ionian vs Dynamism boots sim."""

from simulate_senna_boots import (
    FLASH_BASE,
    ITEMS,
    T3_BOOTS_MINUTE,
    area,
    first_item_minute,
    run_build,
    BUILD_PATHS,
    ROLE_OF,
    self_check,
)


def test_boot_stats():
    assert ITEMS["Boots of Dynamism"].cost == 1200
    assert ITEMS["Boots of Dynamism"].ad == 15
    assert ITEMS["Boots of Dynamism"].flat_apen == 10
    assert ITEMS["Ionian Boots of Lucidity"].cost == 1000
    assert ITEMS["Ionian Boots of Lucidity"].ah == 15
    assert ITEMS["Armorcrusher Boots"].cost == 2200
    assert ITEMS["Armorcrusher Boots"].ad == 20
    assert ITEMS["Armorcrusher Boots"].flat_apen == 10
    assert ITEMS["Armorcrusher Boots"].pct_apen == 0.06
    assert ITEMS["Crimson Lucidity"].cost == 2000
    assert ITEMS["Crimson Lucidity"].ah == 25
    assert ITEMS["Crimson Lucidity"].summoner_haste == 20.0


def test_self_check_and_role_split():
    results = {
        name: run_build(name, path, ROLE_OF[name])
        for name, path in BUILD_PATHS.items()
    }
    self_check(results)
    adc_dyn = results["ADC · Dynamism → Armorcrusher"]
    adc_ion = results["ADC · Ionian → Crimson"]
    # T3 gated.
    assert first_item_minute(adc_dyn, "Armorcrusher Boots") >= T3_BOOTS_MINUTE
    assert first_item_minute(adc_ion, "Crimson Lucidity") >= T3_BOOTS_MINUTE
    # Dynamism is not a Flash boot.
    assert abs(adc_dyn[19].flash_cd - FLASH_BASE) < 1e-6
    assert adc_ion[19].flash_cd < FLASH_BASE
    # Combat vs haste trade.
    assert area(adc_dyn, "combo") > area(adc_ion, "combo")
    assert area(adc_ion, "q_per_min") > area(adc_dyn, "q_per_min")


if __name__ == "__main__":
    test_boot_stats()
    test_self_check_and_role_split()
    print("ok")
