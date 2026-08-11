from argparse import ArgumentParser
from pathlib import Path

from personal_cic.bootstrap import collect_once, create_context
from personal_cic.ui.main.console import render


def main() -> None:
    parser = ArgumentParser(description="Personal CIC self-awareness one-shot diagnostic")
    parser.add_argument(
        "--state",
        default="state/world.json",
        help="durable world-state snapshot path",
    )
    parser.add_argument(
        "--health-config",
        default="config/health.json",
        help="health threshold configuration",
    )
    args = parser.parse_args()

    context = create_context(health_config_path=Path(args.health_config))
    collect_once(context)
    context.world.write_json(Path(args.state))
    render(context.world, context.events.published_count)


if __name__ == "__main__":
    main()
