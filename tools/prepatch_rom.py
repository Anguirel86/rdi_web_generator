"""
This script generates prepatched config and ctrom objects which can be
used later by the randomizer to speed up seed generation.
"""

from ctrando import common, randomizer


def main():
    """
    Apply the base patch to a ROM and save the output.
    This will allow future seed generation calls to skip this step
    and speed up the process.
    """
    base_rom = common.ctrom.CTRom.from_file('./ct.sfc')
    randomizer.dump_openworld_post_config(base_rom, 'post_config.pkl')
    randomizer.dump_prepatched_ctrom(
        vanilla_rom=base_rom, dump_path='prepatched_rom.pkl')


if __name__ == "__main__":
    main()
